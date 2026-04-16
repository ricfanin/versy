package com.example.versy_app.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.Stop
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.runtime.snapshotFlow
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.versy_app.data.ConnectionState
import com.example.versy_app.ui.components.Joystick
import com.example.versy_app.ui.theme.DangerRed
import kotlinx.coroutines.FlowPreview
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.sample
import kotlin.math.abs

@OptIn(FlowPreview::class)
@Composable
fun JoystickScreen(
    connectionState: ConnectionState,
    onMove: (Float, Float) -> Unit,
    onStop: () -> Unit,
    modifier: Modifier = Modifier
) {
    var jx by remember { mutableFloatStateOf(0f) }
    var jy by remember { mutableFloatStateOf(0f) }

    val isConnected = connectionState == ConnectionState.Connected

    LaunchedEffect(isConnected) {
        if (!isConnected) return@LaunchedEffect
        val xFlow = snapshotFlow { jx }
        val yFlow = snapshotFlow { jy }
        xFlow.combine(yFlow) { x, y -> x to y }
            .sample(100)
            .distinctUntilChanged()
            .collect { (x, y) ->
                if (abs(x) > 0.001f || abs(y) > 0.001f) {
                    onMove(x, y)
                }
            }
    }

    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(horizontal = 16.dp, vertical = 12.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        Column {
            Text(
                text = "Pilota",
                style = MaterialTheme.typography.displayLarge,
                color = MaterialTheme.colorScheme.onBackground
            )
            Text(
                text = "Trascina per muovere il robot, rilascia per fermarlo",
                style = MaterialTheme.typography.bodyLarge,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }

        AxisIndicators(x = jx, y = jy)

        Box(
            modifier = Modifier
                .fillMaxWidth()
                .weight(1f),
            contentAlignment = Alignment.Center
        ) {
            Joystick(
                onMove = { x, y ->
                    jx = x
                    jy = y
                },
                onRelease = {
                    jx = 0f
                    jy = 0f
                    onStop()
                }
            )
        }

        Button(
            onClick = {
                jx = 0f; jy = 0f
                onStop()
            },
            enabled = isConnected,
            modifier = Modifier
                .fillMaxWidth()
                .height(68.dp),
            shape = RoundedCornerShape(20.dp),
            colors = ButtonDefaults.buttonColors(
                containerColor = DangerRed,
                contentColor = Color.White,
                disabledContainerColor = DangerRed.copy(alpha = 0.3f)
            )
        ) {
            Icon(Icons.Rounded.Stop, contentDescription = null)
            Spacer(Modifier.width(10.dp))
            Text("STOP EMERGENZA", fontWeight = FontWeight.Bold, fontSize = 18.sp)
        }

        if (!isConnected) {
            Text(
                "Connettiti al robot per inviare comandi",
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.fillMaxWidth(),
                style = MaterialTheme.typography.bodyMedium
            )
        }
    }
}

@Composable
private fun AxisIndicators(x: Float, y: Float) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        AxisBar(label = "X", value = x, modifier = Modifier.weight(1f))
        AxisBar(label = "Y", value = y, modifier = Modifier.weight(1f))
    }
}

@Composable
private fun AxisBar(label: String, value: Float, modifier: Modifier = Modifier) {
    Column(
        modifier = modifier
            .clip(RoundedCornerShape(14.dp))
            .background(
                Brush.horizontalGradient(
                    listOf(
                        MaterialTheme.colorScheme.surface,
                        MaterialTheme.colorScheme.surfaceVariant
                    )
                )
            )
            .padding(horizontal = 14.dp, vertical = 10.dp)
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = label,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                fontWeight = FontWeight.SemiBold
            )
            Text(
                text = "%+.2f".format(value),
                color = MaterialTheme.colorScheme.primary,
                fontWeight = FontWeight.Bold,
                fontSize = 16.sp
            )
        }
        Spacer(Modifier.height(6.dp))
        LinearProgressIndicator(
            progress = { ((value + 1f) / 2f).coerceIn(0f, 1f) },
            modifier = Modifier
                .fillMaxWidth()
                .height(6.dp)
                .clip(RoundedCornerShape(3.dp)),
            color = MaterialTheme.colorScheme.primary,
            trackColor = MaterialTheme.colorScheme.outline.copy(alpha = 0.4f)
        )
    }
}
