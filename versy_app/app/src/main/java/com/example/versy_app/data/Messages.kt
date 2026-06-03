package com.example.versy_app.data

import org.json.JSONArray
import org.json.JSONObject

sealed interface OutboundMessage {
    fun toJson(): String
}

data class MoveMessage(val vx: Float, val vy: Float, val omega: Float) : OutboundMessage {
    override fun toJson(): String = JSONObject()
        .put("type", "move")
        .put("vx", vx.toDouble())
        .put("vy", vy.toDouble())
        .put("omega", omega.toDouble())
        .toString()
}

data object StopMessage : OutboundMessage {
    override fun toJson(): String = JSONObject().put("type", "stop").toString()
}

data class FindArucoMessage(val markerId: Int, val ml: Int) : OutboundMessage {
    override fun toJson(): String = JSONObject()
        .put("type", "find_aruco")
        .put("marker_id", markerId)
        .put("ml", ml)
        .toString()
}

/**
 * Push-to-pour: comando di erogazione manuale "tieni premuto".
 *
 * Inviato alla pressione del pulsante e ripetuto periodicamente come heartbeat finché
 * resta premuto (dead-man's switch). Il robot deve trattarlo come "continua a erogare" e
 * resettare a ogni messaggio il proprio watchdog: se gli heartbeat smettono di arrivare
 * (es. connessione persa) deve fermare l'erogazione anche senza un [PourStopMessage].
 */
data object PourStartMessage : OutboundMessage {
    override fun toJson(): String = JSONObject().put("type", "pour_start").toString()
}

/** Push-to-pour: rilascio del pulsante, ferma l'erogazione manuale. */
data object PourStopMessage : OutboundMessage {
    override fun toJson(): String = JSONObject().put("type", "pour_stop").toString()
}

/**
 * Stato della state machine del robot.
 *
 * Sul protocollo arriva come nome della classe Python ([fromWire]); qui viene mappato
 * a un enum stabile così che la UI non dipenda dai nomi interni del robot.
 */
enum class RobotState {
    INIT, SCAN, MOVING, POURING, RETREAT, UNKNOWN;

    companion object {
        fun fromWire(raw: String): RobotState = when (raw) {
            "InitState" -> INIT
            "ScanState" -> SCAN
            "MovingState" -> MOVING
            "PouringState" -> POURING
            "RetreatState" -> RETREAT
            else -> UNKNOWN
        }
    }
}

/** Un lavoro nella coda del robot o quello attualmente in lavorazione. */
data class RobotJob(val username: String, val markerId: Int)

sealed interface InboundMessage {
    /**
     * Stato completo del robot, broadcast a ogni transizione/cambio coda/connessione
     * e inviato come snapshot al momento della connessione. È la source of truth dell'UI.
     */
    data class RobotStatus(
        val state: RobotState,
        val currentJob: RobotJob?,
        val queue: List<RobotJob>,
        val connectedUsers: List<String>
    ) : InboundMessage

    /** Marker confermato (ScanState -> MovingState). */
    data class ArucoFound(val markerId: Int) : InboundMessage

    /** Marker perso oltre la soglia di retry (MovingState -> ScanState). */
    data class ArucoLost(val markerId: Int) : InboundMessage

    /** Bicchiere rilevato col ToF, versamento concluso (PouringState -> RetreatState). */
    data class PourComplete(val mlPoured: Float) : InboundMessage

    /** Risposta diretta a [FindArucoMessage]: job accodato. */
    data object FindArucoQueued : InboundMessage

    /** Risposta diretta a [StopMessage]. */
    data object StopComplete : InboundMessage

    /** Risposta diretta a [MoveMessage]. */
    data object MoveComplete : InboundMessage

    data class ErrorMsg(val code: String, val message: String) : InboundMessage

    /** Messaggio non riconosciuto o JSON non valido. */
    data class Unknown(val raw: String) : InboundMessage
}

private fun JSONObject.toRobotJob(): RobotJob =
    RobotJob(username = optString("username"), markerId = optInt("marker_id"))

private fun JSONArray.toRobotJobs(): List<RobotJob> =
    (0 until length()).mapNotNull { i -> optJSONObject(i)?.toRobotJob() }

private fun JSONArray.toStringList(): List<String> =
    (0 until length()).map { optString(it) }

fun parseInbound(raw: String): InboundMessage {
    return try {
        val obj = JSONObject(raw)
        when (obj.optString("type")) {
            "robot_status" -> InboundMessage.RobotStatus(
                state = RobotState.fromWire(obj.optString("state")),
                currentJob = obj.optJSONObject("current_job")?.toRobotJob(),
                queue = (obj.optJSONArray("queue") ?: JSONArray()).toRobotJobs(),
                connectedUsers = (obj.optJSONArray("connected_users") ?: JSONArray()).toStringList()
            )
            "aruco_found" -> InboundMessage.ArucoFound(obj.getInt("marker_id"))
            "aruco_lost" -> InboundMessage.ArucoLost(obj.getInt("marker_id"))
            "pour_complete" -> InboundMessage.PourComplete(
                mlPoured = obj.optDouble("ml_poured", 0.0).toFloat()
            )
            "find_aruco_queued" -> InboundMessage.FindArucoQueued
            "stop_complete" -> InboundMessage.StopComplete
            "move_complete" -> InboundMessage.MoveComplete
            "error" -> InboundMessage.ErrorMsg(
                code = obj.optString("code"),
                message = obj.optString("message")
            )
            else -> InboundMessage.Unknown(raw)
        }
    } catch (_: Exception) {
        InboundMessage.Unknown(raw)
    }
}
