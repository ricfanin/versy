package com.example.versy_app.viewmodel

import android.app.Application
import android.content.Context
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.example.versy_app.data.ArucoMarkers
import com.example.versy_app.data.ConnectionState
import com.example.versy_app.data.FindArucoMessage
import com.example.versy_app.data.InboundMessage
import com.example.versy_app.data.MoveMessage
import com.example.versy_app.data.PourStartMessage
import com.example.versy_app.data.PourStopMessage
import com.example.versy_app.data.RobotJob
import com.example.versy_app.data.RobotSocket
import com.example.versy_app.data.RobotState
import com.example.versy_app.data.StopMessage
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch

enum class PourPhase { Idle, Queued, Searching, Approaching, Pouring, Done, Failed }

data class PourStatus(
    val phase: PourPhase = PourPhase.Idle,
    val message: String? = null,
    val queuePosition: Int? = null
)

/**
 * Fasi in cui un versamento richiesto da questo client è in corso e quindi
 * interrompibile dall'utente. La UI la usa sia per lo stato "busy" (pulsante VERSA
 * disabilitato) sia per mostrare il pulsante di interruzione nel progress sheet.
 *
 * `when` esaustivo di proposito: aggiungere una nuova [PourPhase] forza una decisione
 * esplicita invece di ricadere su un default silenzioso.
 */
val PourPhase.isActive: Boolean
    get() = when (this) {
        PourPhase.Queued,
        PourPhase.Searching,
        PourPhase.Approaching,
        PourPhase.Pouring -> true
        PourPhase.Idle,
        PourPhase.Done,
        PourPhase.Failed -> false
    }

class AppViewModel(app: Application) : AndroidViewModel(app) {

    private val prefs = app.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    private val socket = RobotSocket()

    val connectionState: StateFlow<ConnectionState> = socket.connectionState

    private val _address = MutableStateFlow(prefs.getString(KEY_ADDRESS, DEFAULT_ADDRESS) ?: DEFAULT_ADDRESS)
    val address: StateFlow<String> = _address.asStateFlow()

    private val _username = MutableStateFlow(loadOrCreateUsername())
    val username: StateFlow<String> = _username.asStateFlow()

    /** Marker ArUco personalizzati aggiunti dall'utente, persistiti tra le sessioni. */
    private val _customMarkers = MutableStateFlow(loadCustomMarkers())
    val customMarkers: StateFlow<List<Int>> = _customMarkers.asStateFlow()

    /** Ultimo robot_status ricevuto: source of truth per stato, coda e utenti. */
    private val _robotStatus = MutableStateFlow<InboundMessage.RobotStatus?>(null)
    val robotStatus: StateFlow<InboundMessage.RobotStatus?> = _robotStatus.asStateFlow()

    private val _lastError = MutableStateFlow<InboundMessage.ErrorMsg?>(null)
    val lastError: StateFlow<InboundMessage.ErrorMsg?> = _lastError.asStateFlow()

    /** Stato del versamento richiesto da questo client, derivato dai robot_status. */
    private val _pourStatus = MutableStateFlow(PourStatus())
    val pourStatus: StateFlow<PourStatus> = _pourStatus.asStateFlow()

    // Tracking del job richiesto da questo client.
    private var myMarker: Int? = null
    private var myJobSeenActive = false
    private var lastPourMl: Float? = null
    private var pourTerminal = false

    // Heartbeat del push-to-pour: attivo finché il pulsante è premuto.
    private var manualPourJob: Job? = null

    init {
        viewModelScope.launch {
            socket.incoming.collect { msg -> onInbound(msg) }
        }
        viewModelScope.launch {
            connectionState.collect { state ->
                if (state is ConnectionState.Disconnected || state is ConnectionState.Error) {
                    _robotStatus.value = null
                    // Inutile continuare gli heartbeat su una connessione caduta: il watchdog
                    // del robot ferma l'erogazione lato suo.
                    manualPourJob?.cancel()
                    manualPourJob = null
                    if (myMarker != null && !pourTerminal) {
                        setPour(PourPhase.Failed, "Connessione persa")
                    }
                }
            }
        }
    }

    private fun onInbound(msg: InboundMessage) {
        when (msg) {
            is InboundMessage.RobotStatus -> {
                _robotStatus.value = msg
                updatePourFromStatus(msg)
            }
            is InboundMessage.ArucoFound -> {
                if (!pourTerminal && msg.markerId == myMarker) {
                    setPour(PourPhase.Approaching, "Marker trovato, mi avvicino…")
                }
            }
            is InboundMessage.ArucoLost -> {
                if (!pourTerminal && msg.markerId == myMarker) {
                    setPour(PourPhase.Searching, "Marker perso, riprovo…")
                }
            }
            is InboundMessage.PourComplete -> {
                lastPourMl = msg.mlPoured
                if (!pourTerminal && myJobSeenActive) {
                    setPour(PourPhase.Done, doneMessage())
                    pourTerminal = true
                }
            }
            is InboundMessage.ErrorMsg -> {
                _lastError.value = msg
                if (myMarker != null && !pourTerminal) {
                    setPour(PourPhase.Failed, msg.message.ifBlank { msg.code })
                    pourTerminal = true
                }
            }
            InboundMessage.StopComplete -> resetPourStatus()
            InboundMessage.FindArucoQueued,
            InboundMessage.MoveComplete -> Unit
            is InboundMessage.Unknown -> Unit
        }
    }

    private fun updatePourFromStatus(status: InboundMessage.RobotStatus) {
        val marker = myMarker ?: return
        if (pourTerminal) return
        val me = _username.value
        fun isMine(job: RobotJob?) = job != null && job.username == me && job.markerId == marker

        when {
            isMine(status.currentJob) -> {
                myJobSeenActive = true
                when (status.state) {
                    RobotState.SCAN -> setPour(PourPhase.Searching, "Cerco il marker #$marker…")
                    RobotState.MOVING -> setPour(PourPhase.Approaching, "Mi avvicino al marker…")
                    RobotState.POURING -> setPour(PourPhase.Pouring, "Sto versando…")
                    RobotState.RETREAT -> {
                        setPour(PourPhase.Done, doneMessage())
                        pourTerminal = true
                    }
                    else -> setPour(PourPhase.Searching, "In lavorazione…")
                }
            }
            status.queue.any { isMine(it) } -> {
                val pos = status.queue.indexOfFirst { isMine(it) } + 1
                setPour(PourPhase.Queued, "In coda · posizione $pos", queuePosition = pos)
            }
            myJobSeenActive -> {
                // Job sparito da attivo senza essere passato per RetreatState/pour_complete:
                // interruzione anomala (es. stop globale di un altro utente).
                if (lastPourMl != null) {
                    setPour(PourPhase.Done, doneMessage())
                } else {
                    setPour(PourPhase.Failed, "Operazione interrotta")
                }
                pourTerminal = true
            }
            status.state == RobotState.INIT && status.currentJob == null -> {
                // Job rimosso prima di essere servito (es. stop di un altro utente).
                resetPourStatus()
            }
            // altrimenti: job non ancora visibile, mantieni lo stato corrente
        }
    }

    private fun doneMessage(): String =
        lastPourMl?.let { "Versati ${it.toInt()} ml" } ?: "Erogazione completata"

    private fun setPour(phase: PourPhase, message: String?, queuePosition: Int? = null) {
        _pourStatus.value = PourStatus(phase, message, queuePosition)
    }

    private fun loadOrCreateUsername(): String {
        val existing = prefs.getString(KEY_USERNAME, null)
        if (!existing.isNullOrBlank()) return existing
        val generated = "user-" + (1000..9999).random()
        prefs.edit().putString(KEY_USERNAME, generated).apply()
        return generated
    }

    private fun loadCustomMarkers(): List<Int> =
        prefs.getString(KEY_CUSTOM_MARKERS, null)
            ?.split(',')
            ?.mapNotNull { it.trim().toIntOrNull() }
            ?.filter { it in ArucoMarkers.idRange }
            ?.distinct()
            ?: emptyList()

    /** Aggiunge un marker personalizzato (id valido e non già presente) e lo persiste. */
    fun addCustomMarker(id: Int) {
        if (id !in ArucoMarkers.idRange) return
        val current = _customMarkers.value
        if (id in current) return
        val updated = current + id
        _customMarkers.value = updated
        persistCustomMarkers(updated)
    }

    /** Rimuove un marker personalizzato e persiste la lista aggiornata. */
    fun removeCustomMarker(id: Int) {
        val current = _customMarkers.value
        val updated = current.filterNot { it == id }
        if (updated.size == current.size) return
        _customMarkers.value = updated
        persistCustomMarkers(updated)
    }

    private fun persistCustomMarkers(ids: List<Int>) {
        prefs.edit().putString(KEY_CUSTOM_MARKERS, ids.joinToString(",")).apply()
    }

    fun updateAddress(value: String) {
        _address.value = value
        prefs.edit().putString(KEY_ADDRESS, value).apply()
    }

    fun updateUsername(value: String) {
        val v = value.trim()
        if (v.isBlank() || v == _username.value) return
        _username.value = v
        prefs.edit().putString(KEY_USERNAME, v).apply()
        // Lo username è nella query string del WS: per applicarlo serve riconnettere.
        val state = connectionState.value
        if (state == ConnectionState.Connected || state == ConnectionState.Connecting) {
            socket.connect(_address.value, v)
        }
    }

    fun connect() {
        socket.connect(_address.value, _username.value)
    }

    fun disconnect() {
        socket.disconnect()
    }

    fun sendMove(vx: Float, vy: Float, omega: Float) {
        socket.send(MoveMessage(vx, vy, omega))
    }

    fun sendStop() {
        socket.send(StopMessage)
    }

    /**
     * Interrompe il versamento richiesto da questo client: invia uno stop al robot e
     * azzera subito lo stato locale per dare feedback immediato (chiusura del progress
     * sheet). Lo stop_complete e il successivo robot_status confermano l'interruzione
     * lato robot; l'azzeramento di [myMarker] evita che uno status "in volo" riattivi
     * il job.
     */
    fun stopPour() {
        socket.send(StopMessage)
        resetPourStatus()
    }

    /**
     * Push-to-pour: inizio dell'erogazione manuale (pressione del pulsante).
     *
     * Invia subito un [PourStartMessage] e lo ripete come heartbeat ogni
     * [MANUAL_POUR_HEARTBEAT_MS] finché [stopManualPour] non viene chiamato. L'heartbeat è
     * un dead-man's switch: se la connessione cade mentre il pulsante è premuto, il robot
     * smette di ricevere messaggi e (tramite il proprio watchdog) deve fermare l'erogazione.
     * Idempotente: chiamate ripetute non avviano heartbeat multipli.
     */
    fun startManualPour() {
        if (manualPourJob?.isActive == true) return
        manualPourJob = viewModelScope.launch {
            while (isActive) {
                socket.send(PourStartMessage)
                delay(MANUAL_POUR_HEARTBEAT_MS)
            }
        }
    }

    /**
     * Push-to-pour: fine dell'erogazione manuale (rilascio del pulsante). Ferma l'heartbeat
     * e invia un [PourStopMessage]. Idempotente: sicuro da chiamare anche se non si stava
     * erogando (es. al dispose della schermata), così il robot riceve sempre lo stop.
     */
    fun stopManualPour() {
        manualPourJob?.cancel()
        manualPourJob = null
        socket.send(PourStopMessage)
    }

    /**
     * Richiede al robot di servire un marker versando [ml] millilitri. Il robot esegue
     * l'intero ciclo (scan -> avvicinamento -> versamento -> ritorno) autonomamente; il
     * progresso viene seguito tramite i robot_status broadcast.
     */
    fun requestPour(markerId: Int, ml: Int) {
        val sent = socket.send(FindArucoMessage(markerId, ml))
        if (!sent) {
            setPour(PourPhase.Failed, "Non connesso")
            return
        }
        myMarker = markerId
        myJobSeenActive = false
        lastPourMl = null
        pourTerminal = false
        setPour(PourPhase.Searching, "Richiesta inviata…")
    }

    fun resetPourStatus() {
        myMarker = null
        myJobSeenActive = false
        lastPourMl = null
        pourTerminal = false
        _pourStatus.value = PourStatus()
    }

    override fun onCleared() {
        super.onCleared()
        socket.close()
    }

    companion object {
        private const val PREFS_NAME = "versy_prefs"
        private const val KEY_ADDRESS = "ws_address"
        private const val KEY_USERNAME = "ws_username"
        private const val KEY_CUSTOM_MARKERS = "custom_markers"
        private const val DEFAULT_ADDRESS = "10.0.2.2:8765"

        /** Intervallo di re-invio del [PourStartMessage] mentre il pulsante è premuto. */
        private const val MANUAL_POUR_HEARTBEAT_MS = 250L
    }
}
