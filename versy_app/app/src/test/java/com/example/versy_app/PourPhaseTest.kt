package com.example.versy_app

import com.example.versy_app.viewmodel.PourPhase
import com.example.versy_app.viewmodel.isActive
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Test del contratto [PourPhase.isActive], che governa sia lo stato "busy" della
 * PourScreen (pulsante VERSA disabilitato) sia la presenza del pulsante "Interrompi"
 * nel progress sheet. Logica pura, nessuna dipendenza Android.
 */
class PourPhaseTest {

    /** Fasi in cui un versamento è in corso e quindi interrompibile. */
    private val activePhases = setOf(
        PourPhase.Queued,
        PourPhase.Searching,
        PourPhase.Approaching,
        PourPhase.Pouring
    )

    @Test
    fun activePhases_areActive() {
        for (phase in activePhases) {
            assertTrue("$phase dovrebbe essere attiva", phase.isActive)
        }
    }

    @Test
    fun idleAndTerminalPhases_areNotActive() {
        for (phase in listOf(PourPhase.Idle, PourPhase.Done, PourPhase.Failed)) {
            assertFalse("$phase non dovrebbe essere attiva", phase.isActive)
        }
    }

    /**
     * Esaustività: esattamente le fasi in [activePhases] sono attive su tutto l'enum.
     * Blocca regressioni se in futuro si aggiunge una nuova PourPhase senza decidere
     * il suo stato di interrompibilità.
     */
    @Test
    fun isActive_matchesExactlyTheActiveSet() {
        val computed = PourPhase.entries.filter { it.isActive }.toSet()
        assertEquals(activePhases, computed)
    }
}
