package com.example.versy_app.viewmodel

import android.app.Application
import android.content.Context
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.example.versy_app.data.ConnectionState
import com.example.versy_app.data.FindArucoMessage
import com.example.versy_app.data.InboundMessage
import com.example.versy_app.data.MoveMessage
import com.example.versy_app.data.PourMessage
import com.example.versy_app.data.RobotSocket
import com.example.versy_app.data.StopMessage
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.filterIsInstance
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch
import kotlinx.coroutines.withTimeoutOrNull

enum class PourPhase { Idle, Searching, Pouring, Complete, Failed }

data class PourStatus(
    val phase: PourPhase = PourPhase.Idle,
    val message: String? = null
)

class AppViewModel(app: Application) : AndroidViewModel(app) {

    private val prefs = app.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    private val socket = RobotSocket()

    val connectionState: StateFlow<ConnectionState> = socket.connectionState

    private val _address = MutableStateFlow(prefs.getString(KEY_ADDRESS, DEFAULT_ADDRESS) ?: DEFAULT_ADDRESS)
    val address: StateFlow<String> = _address.asStateFlow()

    private val _lastAruco = MutableStateFlow<InboundMessage.ArucoFound?>(null)
    val lastAruco: StateFlow<InboundMessage.ArucoFound?> = _lastAruco.asStateFlow()

    private val _lastPour = MutableStateFlow<InboundMessage.PourComplete?>(null)
    val lastPour: StateFlow<InboundMessage.PourComplete?> = _lastPour.asStateFlow()

    private val _lastStatus = MutableStateFlow<InboundMessage.Status?>(null)
    val lastStatus: StateFlow<InboundMessage.Status?> = _lastStatus.asStateFlow()

    private val _lastError = MutableStateFlow<InboundMessage.ErrorMsg?>(null)
    val lastError: StateFlow<InboundMessage.ErrorMsg?> = _lastError.asStateFlow()

    private val _pourStatus = MutableStateFlow(PourStatus())
    val pourStatus: StateFlow<PourStatus> = _pourStatus.asStateFlow()

    private var pourJob: Job? = null

    init {
        viewModelScope.launch {
            socket.incoming.collect { msg ->
                when (msg) {
                    is InboundMessage.ArucoFound -> _lastAruco.value = msg
                    is InboundMessage.PourComplete -> _lastPour.value = msg
                    is InboundMessage.Status -> _lastStatus.value = msg
                    is InboundMessage.ErrorMsg -> _lastError.value = msg
                    is InboundMessage.Unknown -> { /* ignore */ }
                }
            }
        }
    }

    fun updateAddress(value: String) {
        _address.value = value
        prefs.edit().putString(KEY_ADDRESS, value).apply()
    }

    fun connect() {
        socket.connect(_address.value)
    }

    fun disconnect() {
        socket.disconnect()
    }

    fun sendMove(x: Float, y: Float) {
        socket.send(MoveMessage(x, y))
    }

    fun sendStop() {
        socket.send(StopMessage)
    }

    fun sendFindAndPour(markerId: Int, ml: Int) {
        pourJob?.cancel()
        pourJob = viewModelScope.launch {
            _pourStatus.value = PourStatus(PourPhase.Searching, "Ricerca marker $markerId…")
            val sent = socket.send(FindArucoMessage(markerId))
            if (!sent) {
                _pourStatus.value = PourStatus(PourPhase.Failed, "Non connesso")
                return@launch
            }
            val found = withTimeoutOrNull(FIND_TIMEOUT_MS) {
                socket.incoming
                    .filterIsInstance<InboundMessage.ArucoFound>()
                    .first { it.markerId == markerId }
            }
            if (found == null) {
                _pourStatus.value = PourStatus(PourPhase.Failed, "Marker $markerId non trovato")
                return@launch
            }
            _pourStatus.value = PourStatus(PourPhase.Pouring, "Versando $ml ml…")
            socket.send(PourMessage(ml))
            val complete = withTimeoutOrNull(POUR_TIMEOUT_MS) {
                socket.incoming.filterIsInstance<InboundMessage.PourComplete>().first()
            }
            _pourStatus.value = if (complete != null) {
                PourStatus(PourPhase.Complete, "Versati ${complete.mlPoured.toInt()} ml")
            } else {
                PourStatus(PourPhase.Failed, "Timeout versamento")
            }
        }
    }

    fun resetPourStatus() {
        _pourStatus.value = PourStatus()
    }

    override fun onCleared() {
        super.onCleared()
        socket.close()
    }

    companion object {
        private const val PREFS_NAME = "versy_prefs"
        private const val KEY_ADDRESS = "ws_address"
        private const val DEFAULT_ADDRESS = "10.0.2.2:8765"
        private const val FIND_TIMEOUT_MS = 15_000L
        private const val POUR_TIMEOUT_MS = 30_000L
    }
}
