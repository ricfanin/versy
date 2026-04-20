package com.example.versy_app.ui.components

import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.gestures.awaitEachGesture
import androidx.compose.foundation.gestures.awaitFirstDown
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.size
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import kotlin.math.atan2
import kotlin.math.cos
import kotlin.math.min
import kotlin.math.sin

private const val USABLE_ANGLE_DEG = 135f

@Composable
fun YawDial(
    modifier: Modifier = Modifier,
    diameter: Dp = 220.dp,
    onChange: (yaw: Float) -> Unit,
    onRelease: () -> Unit
) {
    var dragging by remember { mutableStateOf(false) }
    var rawYaw by remember { mutableFloatStateOf(0f) }

    val animatedYaw by animateFloatAsState(
        targetValue = if (dragging) rawYaw else 0f,
        animationSpec = tween(durationMillis = if (dragging) 0 else 220),
        label = "yawValue"
    )

    val primary = MaterialTheme.colorScheme.primary
    val primaryDim = MaterialTheme.colorScheme.primaryContainer
    val outline = MaterialTheme.colorScheme.outline
    val surface = MaterialTheme.colorScheme.surface

    Box(
        modifier = modifier
            .size(diameter)
            .pointerInput(Unit) {
                awaitEachGesture {
                    val down = awaitFirstDown(requireUnconsumed = false)
                    dragging = true
                    val center = Offset(this.size.width / 2f, this.size.height / 2f)
                    rawYaw = yawFromTouch(down.position, center)
                    onChange(rawYaw)
                    while (true) {
                        val event = awaitPointerEvent()
                        val change = event.changes.firstOrNull { it.id == down.id }
                            ?: event.changes.firstOrNull() ?: break
                        if (!change.pressed) {
                            dragging = false
                            rawYaw = 0f
                            onRelease()
                            break
                        }
                        rawYaw = yawFromTouch(change.position, center)
                        onChange(rawYaw)
                        change.consume()
                    }
                }
            },
        contentAlignment = Alignment.Center
    ) {
        Canvas(modifier = Modifier.fillMaxSize()) {
            val center = Offset(size.width / 2f, size.height / 2f)
            val outerR = min(size.width, size.height) / 2f - 6f
            val trackR = outerR * 0.82f
            val handleR = outerR * 0.16f

            drawCircle(
                brush = Brush.radialGradient(
                    colors = listOf(surface, Color.Black.copy(alpha = 0.5f)),
                    center = center,
                    radius = outerR
                ),
                radius = outerR,
                center = center
            )
            drawCircle(
                color = outline,
                radius = outerR - 1f,
                center = center,
                style = Stroke(width = 3f)
            )

            val startArcAngle = -90f - USABLE_ANGLE_DEG
            val sweep = USABLE_ANGLE_DEG * 2f
            val arcTopLeft = Offset(center.x - trackR, center.y - trackR)
            val arcSize = Size(trackR * 2f, trackR * 2f)
            drawArc(
                color = outline.copy(alpha = 0.8f),
                startAngle = startArcAngle,
                sweepAngle = sweep,
                useCenter = false,
                topLeft = arcTopLeft,
                size = arcSize,
                style = Stroke(width = 4f, cap = StrokeCap.Round)
            )

            val yawDeg = animatedYaw * USABLE_ANGLE_DEG
            val activeStart = -90f
            val activeSweep = yawDeg
            drawArc(
                color = primary.copy(alpha = 0.85f),
                startAngle = activeStart,
                sweepAngle = activeSweep,
                useCenter = false,
                topLeft = arcTopLeft,
                size = arcSize,
                style = Stroke(width = 6f, cap = StrokeCap.Round)
            )

            drawLine(
                color = outline.copy(alpha = 0.5f),
                start = Offset(center.x, center.y - trackR - 10f),
                end = Offset(center.x, center.y - trackR + 10f),
                strokeWidth = 3f,
                cap = StrokeCap.Round
            )

            val yawRad = Math.toRadians((yawDeg - 90f).toDouble())
            val handleCenter = Offset(
                x = center.x + (trackR * cos(yawRad)).toFloat(),
                y = center.y + (trackR * sin(yawRad)).toFloat()
            )

            if (dragging) {
                drawCircle(
                    color = primary.copy(alpha = 0.22f),
                    radius = handleR * 1.5f,
                    center = handleCenter
                )
            }
            drawCircle(
                brush = Brush.radialGradient(
                    colors = listOf(primary, primaryDim),
                    center = handleCenter,
                    radius = handleR
                ),
                radius = handleR,
                center = handleCenter
            )
            drawCircle(
                color = Color.White.copy(alpha = 0.22f),
                radius = handleR * 0.5f,
                center = Offset(handleCenter.x - handleR * 0.25f, handleCenter.y - handleR * 0.25f)
            )
        }
    }
}

private fun yawFromTouch(touch: Offset, center: Offset): Float {
    val dx = touch.x - center.x
    val dy = touch.y - center.y
    if (dx == 0f && dy == 0f) return 0f
    if (dy > 0f) {
        return if (dx >= 0f) 1f else -1f
    }
    val angleRad = atan2(dx.toDouble(), -dy.toDouble())
    val angleDeg = Math.toDegrees(angleRad).toFloat()
    return (angleDeg / USABLE_ANGLE_DEG).coerceIn(-1f, 1f)
}
