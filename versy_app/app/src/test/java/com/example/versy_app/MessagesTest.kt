package com.example.versy_app

import com.example.versy_app.data.FindArucoMessage
import com.example.versy_app.data.InboundMessage
import com.example.versy_app.data.MoveMessage
import com.example.versy_app.data.PourStartMessage
import com.example.versy_app.data.PourStopMessage
import com.example.versy_app.data.RobotState
import com.example.versy_app.data.StopMessage
import com.example.versy_app.data.parseInbound
import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Test del layer protocollo (Messages.kt). Verifica parsing inbound e serializzazione
 * outbound rispetto alla specifica WebSocket del robot.
 *
 * Usa la dipendenza reale org.json (testImplementation), non lo stub di android.jar.
 */
class MessagesTest {

    // --- robot_status (source of truth) ---

    /**
     * Scenario: stato completo con job corrente, coda e utenti.
     *   Given un robot_status con current_job, 2 job in coda e 3 utenti
     *   When viene parsato
     *   Then tutti i campi sono ricostruiti fedelmente e lo stato è mappato a enum
     */
    @Test
    fun parse_robotStatus_full() {
        val raw = """
            {
              "type": "robot_status",
              "state": "ScanState",
              "current_job": { "username": "utente3", "marker_id": 5 },
              "queue": [
                { "username": "utente1", "marker_id": 1 },
                { "username": "utente2", "marker_id": 7 }
              ],
              "connected_users": ["utente1", "utente2", "utente3"]
            }
        """.trimIndent()

        val msg = parseInbound(raw)
        assertTrue(msg is InboundMessage.RobotStatus)
        msg as InboundMessage.RobotStatus

        assertEquals(RobotState.SCAN, msg.state)
        assertEquals("utente3", msg.currentJob?.username)
        assertEquals(5, msg.currentJob?.markerId)
        assertEquals(2, msg.queue.size)
        assertEquals("utente1", msg.queue[0].username)
        assertEquals(1, msg.queue[0].markerId)
        assertEquals(7, msg.queue[1].markerId)
        assertEquals(listOf("utente1", "utente2", "utente3"), msg.connectedUsers)
    }

    /**
     * Scenario: robot idle (snapshot iniziale tipico al connect).
     *   Given current_job null e coda vuota
     *   Then currentJob è null e la coda è vuota
     */
    @Test
    fun parse_robotStatus_idle() {
        val raw = """{"type":"robot_status","state":"InitState","current_job":null,"queue":[],"connected_users":["utente3"]}"""
        val msg = parseInbound(raw) as InboundMessage.RobotStatus

        assertEquals(RobotState.INIT, msg.state)
        assertNull(msg.currentJob)
        assertTrue(msg.queue.isEmpty())
        assertEquals(listOf("utente3"), msg.connectedUsers)
    }

    @Test
    fun parse_robotStatus_allKnownStatesMapped() {
        val pairs = mapOf(
            "InitState" to RobotState.INIT,
            "ScanState" to RobotState.SCAN,
            "MovingState" to RobotState.MOVING,
            "PouringState" to RobotState.POURING,
            "RetreatState" to RobotState.RETREAT
        )
        for ((wire, expected) in pairs) {
            val msg = parseInbound("""{"type":"robot_status","state":"$wire"}""") as InboundMessage.RobotStatus
            assertEquals("stato $wire", expected, msg.state)
        }
    }

    @Test
    fun parse_robotStatus_unknownStateFallsBack() {
        val msg = parseInbound("""{"type":"robot_status","state":"SomethingNew"}""") as InboundMessage.RobotStatus
        assertEquals(RobotState.UNKNOWN, msg.state)
        // campi opzionali assenti: difensivi, non devono lanciare
        assertNull(msg.currentJob)
        assertTrue(msg.queue.isEmpty())
        assertTrue(msg.connectedUsers.isEmpty())
    }

    // --- aruco_found: regressione del bug critico ---

    /**
     * Scenario: aruco_found ha SOLO marker_id (regressione del bug che parsava
     * distance_cm/angle_deg inesistenti, facendolo finire in Unknown).
     */
    @Test
    fun parse_arucoFound_onlyMarkerId() {
        val msg = parseInbound("""{"type":"aruco_found","marker_id":5}""")
        assertTrue("aruco_found non deve finire in Unknown", msg is InboundMessage.ArucoFound)
        assertEquals(5, (msg as InboundMessage.ArucoFound).markerId)
    }

    @Test
    fun parse_arucoLost() {
        val msg = parseInbound("""{"type":"aruco_lost","marker_id":5}""")
        assertEquals(5, (msg as InboundMessage.ArucoLost).markerId)
    }

    // --- pour_complete ---

    @Test
    fun parse_pourComplete() {
        val msg = parseInbound("""{"type":"pour_complete","ml_poured":30.0}""")
        assertEquals(30.0f, (msg as InboundMessage.PourComplete).mlPoured, 0.001f)
    }

    @Test
    fun parse_pourComplete_missingMlDefaultsToZero() {
        val msg = parseInbound("""{"type":"pour_complete"}""")
        assertEquals(0.0f, (msg as InboundMessage.PourComplete).mlPoured, 0.001f)
    }

    // --- risposte dirette ---

    @Test
    fun parse_directResponses() {
        assertEquals(InboundMessage.FindArucoQueued, parseInbound("""{"type":"find_aruco_queued"}"""))
        assertEquals(InboundMessage.StopComplete, parseInbound("""{"type":"stop_complete"}"""))
        assertEquals(InboundMessage.MoveComplete, parseInbound("""{"type":"move_complete"}"""))
    }

    // --- error ---

    @Test
    fun parse_error() {
        val msg = parseInbound("""{"type":"error","code":"ARUCO_FINDING_ERROR","message":"boom"}""")
        msg as InboundMessage.ErrorMsg
        assertEquals("ARUCO_FINDING_ERROR", msg.code)
        assertEquals("boom", msg.message)
    }

    // --- robustezza ---

    @Test
    fun parse_malformedJson_isUnknown() {
        val raw = "{ not json"
        val msg = parseInbound(raw)
        assertTrue(msg is InboundMessage.Unknown)
        assertEquals(raw, (msg as InboundMessage.Unknown).raw)
    }

    @Test
    fun parse_unknownType_isUnknown() {
        val msg = parseInbound("""{"type":"some_future_event","foo":1}""")
        assertTrue(msg is InboundMessage.Unknown)
    }

    // --- outbound (round-trip) ---

    @Test
    fun serialize_move() {
        val json = JSONObject(MoveMessage(vx = 0f, vy = 30f, omega = 0f).toJson())
        assertEquals("move", json.getString("type"))
        assertEquals(0.0, json.getDouble("vx"), 0.001)
        assertEquals(30.0, json.getDouble("vy"), 0.001)
        assertEquals(0.0, json.getDouble("omega"), 0.001)
    }

    @Test
    fun serialize_findAruco() {
        val json = JSONObject(FindArucoMessage(markerId = 5, ml = 100).toJson())
        assertEquals("find_aruco", json.getString("type"))
        assertEquals(5, json.getInt("marker_id"))
        assertEquals(100, json.getInt("ml"))
    }

    @Test
    fun serialize_stop() {
        val json = JSONObject(StopMessage.toJson())
        assertEquals("stop", json.getString("type"))
    }

    @Test
    fun serialize_pourStart() {
        val json = JSONObject(PourStartMessage.toJson())
        assertEquals("pour_start", json.getString("type"))
    }

    @Test
    fun serialize_pourStop() {
        val json = JSONObject(PourStopMessage.toJson())
        assertEquals("pour_stop", json.getString("type"))
    }
}
