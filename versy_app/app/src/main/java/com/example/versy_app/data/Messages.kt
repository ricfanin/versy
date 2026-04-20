package com.example.versy_app.data

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

data class FindArucoMessage(val markerId: Int) : OutboundMessage {
    override fun toJson(): String = JSONObject()
        .put("type", "find_aruco")
        .put("marker_id", markerId)
        .toString()
}

data class PourMessage(val ml: Int) : OutboundMessage {
    override fun toJson(): String = JSONObject()
        .put("type", "pour")
        .put("ml", ml)
        .toString()
}

sealed interface InboundMessage {
    data class Status(
        val state: String,
        val battery: Int?,
        val message: String?
    ) : InboundMessage

    data class ArucoFound(
        val markerId: Int,
        val distanceCm: Float,
        val angleDeg: Float
    ) : InboundMessage

    data class PourComplete(val mlPoured: Float) : InboundMessage

    data class ErrorMsg(val code: String, val message: String) : InboundMessage

    data class Unknown(val raw: String) : InboundMessage
}

fun parseInbound(raw: String): InboundMessage {
    return try {
        val obj = JSONObject(raw)
        when (obj.optString("type")) {
            "status" -> InboundMessage.Status(
                state = obj.optString("state"),
                battery = if (obj.has("battery") && !obj.isNull("battery")) obj.getInt("battery") else null,
                message = if (obj.has("message") && !obj.isNull("message")) obj.getString("message") else null
            )
            "aruco_found" -> InboundMessage.ArucoFound(
                markerId = obj.getInt("marker_id"),
                distanceCm = obj.getDouble("distance_cm").toFloat(),
                angleDeg = obj.getDouble("angle_deg").toFloat()
            )
            "pour_complete" -> InboundMessage.PourComplete(
                mlPoured = obj.getDouble("ml_poured").toFloat()
            )
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
