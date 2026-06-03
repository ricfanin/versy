package com.example.versy_app.ui.components

import androidx.compose.foundation.Canvas
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import com.example.versy_app.data.ArucoMarkers

/**
 * Disegna il vero marker ArUco DICT_4X4_50 corrispondente a [id], su fondo bianco
 * con una quiet zone. Se l'id è fuori dal dizionario disegna un placeholder.
 *
 * Il pattern è quello reale riconosciuto dal robot (vedi [ArucoMarkers]).
 */
@Composable
fun ArucoMarkerGraphic(
    id: Int,
    modifier: Modifier = Modifier,
    quietZoneRatio: Float = 0.12f
) {
    val pattern = ArucoMarkers.pattern(id)
    Canvas(modifier = modifier) {
        // Sfondo bianco (incluso quiet zone) per leggibilità e scansionabilità.
        drawRect(color = Color.White, size = size)

        val side = minOf(size.width, size.height)
        val quiet = side * quietZoneRatio
        val markerSide = side - 2 * quiet
        val originX = (size.width - markerSide) / 2f
        val originY = (size.height - markerSide) / 2f
        val cell = markerSide / ArucoMarkers.GRID

        if (pattern != null) {
            for (r in 0 until ArucoMarkers.GRID) {
                for (c in 0 until ArucoMarkers.GRID) {
                    if (pattern[r * ArucoMarkers.GRID + c] == '0') {
                        drawRect(
                            color = Color.Black,
                            topLeft = Offset(originX + c * cell, originY + r * cell),
                            // overdraw di mezzo px per evitare hairline tra celle adiacenti
                            size = Size(cell + 0.5f, cell + 0.5f)
                        )
                    }
                }
            }
        } else {
            // Id non nel dizionario: cornice tratteggiata come placeholder.
            drawRect(
                color = Color(0xFFBDBDBD),
                topLeft = Offset(originX, originY),
                size = Size(markerSide, markerSide),
                style = Stroke(width = cell * 0.4f)
            )
        }
    }
}
