package com.example.versy_app.ui.components

import androidx.compose.animation.core.Spring
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.spring
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.scale
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

@Composable
fun ArucoMarkerTile(
    id: Int,
    selected: Boolean,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    val scale by animateFloatAsState(
        targetValue = if (selected) 1.04f else 1f,
        animationSpec = spring(dampingRatio = Spring.DampingRatioMediumBouncy),
        label = "tileScale"
    )

    val borderColor = if (selected) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.outline
    val containerColor = if (selected)
        MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.35f)
    else
        MaterialTheme.colorScheme.surfaceVariant

    Surface(
        modifier = modifier
            .scale(scale)
            .clip(RoundedCornerShape(18.dp))
            .clickable { onClick() },
        shape = RoundedCornerShape(18.dp),
        color = containerColor,
        border = BorderStroke(if (selected) 2.dp else 1.dp, borderColor)
    ) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .aspectRatio(1f)
                .padding(10.dp),
            contentAlignment = Alignment.Center
        ) {
            MarkerFrame(
                modifier = Modifier.fillMaxSize()
            )
            Text(
                text = "#$id",
                fontSize = 22.sp,
                fontFamily = FontFamily.Monospace,
                fontWeight = FontWeight.Bold,
                color = if (selected) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurface
            )
        }
    }
}

@Composable
private fun MarkerFrame(modifier: Modifier = Modifier) {
    val frame = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.9f)
    val inner = MaterialTheme.colorScheme.surface

    Box(
        modifier = modifier
            .clip(RoundedCornerShape(8.dp))
            .background(frame)
            .padding(6.dp)
    ) {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .clip(RoundedCornerShape(4.dp))
                .background(inner)
        ) {
            CornerDots(color = frame)
        }
    }
}

@Composable
private fun CornerDots(color: Color) {
    Box(modifier = Modifier.fillMaxSize()) {
        val dotModifier = Modifier
            .padding(4.dp)
            .clip(RoundedCornerShape(2.dp))

        Box(
            modifier = dotModifier
                .align(Alignment.TopStart)
                .background(color)
                .padding(5.dp)
        )
        Box(
            modifier = dotModifier
                .align(Alignment.TopEnd)
                .background(color)
                .padding(5.dp)
        )
        Box(
            modifier = dotModifier
                .align(Alignment.BottomStart)
                .background(color)
                .padding(5.dp)
        )
        Box(
            modifier = dotModifier
                .align(Alignment.BottomEnd)
                .background(color)
                .padding(5.dp)
        )
    }
}
