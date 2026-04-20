package com.example.versy_app.ui.components

import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.gestures.awaitEachGesture
import androidx.compose.foundation.gestures.awaitFirstDown
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.size
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import kotlin.math.hypot
import kotlin.math.min

@Composable
fun OmniJoystick(
    modifier: Modifier = Modifier,
    size: Dp = 240.dp,
    onMove: (vx: Float, vy: Float) -> Unit,
    onRelease: () -> Unit
) {
    var dragging by remember { mutableStateOf(false) }
    var rawOffset by remember { mutableStateOf(Offset.Zero) }

    val animatedX by animateFloatAsState(
        targetValue = if (dragging) rawOffset.x else 0f,
        animationSpec = tween(durationMillis = if (dragging) 0 else 220),
        label = "omniX"
    )
    val animatedY by animateFloatAsState(
        targetValue = if (dragging) rawOffset.y else 0f,
        animationSpec = tween(durationMillis = if (dragging) 0 else 220),
        label = "omniY"
    )

    val primary = MaterialTheme.colorScheme.primary
    val primaryDim = MaterialTheme.colorScheme.primaryContainer
    val outline = MaterialTheme.colorScheme.outline
    val surface = MaterialTheme.colorScheme.surface

    val density = LocalDensity.current
    val sizePx = with(density) { size.toPx() }
    val stickRadiusPx = sizePx * 0.30f / 2f
    val maxDrag = sizePx / 2f - stickRadiusPx

    Box(
        modifier = modifier
            .size(size)
            .pointerInput(Unit) {
                awaitEachGesture {
                    val down = awaitFirstDown(requireUnconsumed = false)
                    dragging = true
                    val center = Offset(this.size.width / 2f, this.size.height / 2f)
                    val clamped = clampToCircle(down.position - center, maxDrag)
                    rawOffset = clamped
                    onMove(
                        (clamped.x / maxDrag).coerceIn(-1f, 1f),
                        (-clamped.y / maxDrag).coerceIn(-1f, 1f)
                    )
                    while (true) {
                        val event = awaitPointerEvent()
                        val change = event.changes.firstOrNull { it.id == down.id }
                            ?: event.changes.firstOrNull() ?: break
                        if (!change.pressed) {
                            dragging = false
                            rawOffset = Offset.Zero
                            onRelease()
                            break
                        }
                        val moved = clampToCircle(change.position - center, maxDrag)
                        rawOffset = moved
                        onMove(
                            (moved.x / maxDrag).coerceIn(-1f, 1f),
                            (-moved.y / maxDrag).coerceIn(-1f, 1f)
                        )
                        change.consume()
                    }
                }
            },
        contentAlignment = Alignment.Center
    ) {
        Canvas(modifier = Modifier.size(size)) {
            val center = Offset(this.size.width / 2f, this.size.height / 2f)
            val r = min(this.size.width, this.size.height) / 2f
            val stickR = r * 0.30f

            drawCircle(
                brush = Brush.radialGradient(
                    colors = listOf(surface, Color.Black.copy(alpha = 0.6f)),
                    center = center,
                    radius = r
                ),
                radius = r,
                center = center
            )
            drawCircle(
                color = outline,
                radius = r - 2f,
                center = center,
                style = Stroke(width = 3f)
            )
            drawCircle(
                color = primary.copy(alpha = 0.14f),
                radius = r * 0.55f,
                center = center,
                style = Stroke(width = 2f, cap = StrokeCap.Round)
            )
            drawLine(
                color = outline.copy(alpha = 0.45f),
                start = Offset(center.x - r * 0.6f, center.y),
                end = Offset(center.x + r * 0.6f, center.y),
                strokeWidth = 1.5f
            )
            drawLine(
                color = outline.copy(alpha = 0.45f),
                start = Offset(center.x, center.y - r * 0.6f),
                end = Offset(center.x, center.y + r * 0.6f),
                strokeWidth = 1.5f
            )

            val stickCenter = Offset(center.x + animatedX, center.y + animatedY)

            if (dragging) {
                drawCircle(
                    color = primary.copy(alpha = 0.22f),
                    radius = stickR * 1.6f,
                    center = stickCenter
                )
            }
            drawCircle(
                brush = Brush.radialGradient(
                    colors = listOf(primary, primaryDim),
                    center = stickCenter,
                    radius = stickR
                ),
                radius = stickR,
                center = stickCenter
            )
            drawCircle(
                color = Color.White.copy(alpha = 0.22f),
                radius = stickR * 0.52f,
                center = Offset(stickCenter.x - stickR * 0.25f, stickCenter.y - stickR * 0.25f)
            )
        }
    }
}

private fun clampToCircle(offset: Offset, maxRadius: Float): Offset {
    val dist = hypot(offset.x, offset.y)
    return if (dist <= maxRadius) offset
    else Offset(offset.x / dist * maxRadius, offset.y / dist * maxRadius)
}
