package com.example.versy_app.ui.screens

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.Crossfade
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.CheckCircle
import androidx.compose.material.icons.rounded.ErrorOutline
import androidx.compose.material.icons.rounded.LocalDrink
import androidx.compose.material.icons.rounded.MyLocation
import androidx.compose.material.icons.rounded.Rotate90DegreesCcw
import androidx.compose.material3.AssistChip
import androidx.compose.material3.AssistChipDefaults
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ElevatedCard
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Slider
import androidx.compose.material3.SliderDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.foundation.text.KeyboardOptions
import com.example.versy_app.data.ConnectionState
import com.example.versy_app.data.InboundMessage
import com.example.versy_app.ui.theme.DangerRed
import com.example.versy_app.ui.theme.SuccessGreen
import com.example.versy_app.viewmodel.PourPhase
import com.example.versy_app.viewmodel.PourStatus

@Composable
fun PourScreen(
    connectionState: ConnectionState,
    lastAruco: InboundMessage.ArucoFound?,
    pourStatus: PourStatus,
    onFindAndPour: (markerId: Int, ml: Int) -> Unit,
    modifier: Modifier = Modifier
) {
    var markerInput by remember { mutableStateOf("") }
    var ml by remember { mutableFloatStateOf(100f) }

    val isConnected = connectionState == ConnectionState.Connected
    val isBusy = pourStatus.phase == PourPhase.Searching || pourStatus.phase == PourPhase.Pouring

    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 16.dp)
            .padding(top = 4.dp, bottom = 16.dp)
    ) {
        HeaderBlock()

        Spacer(Modifier.height(16.dp))

        ElevatedCard(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(20.dp)
        ) {
            Column(Modifier.padding(18.dp)) {
                SectionTitle("Marker ArUco")
                Spacer(Modifier.height(10.dp))
                OutlinedTextField(
                    value = markerInput,
                    onValueChange = { v -> markerInput = v.filter { it.isDigit() }.take(5) },
                    label = { Text("ID marker") },
                    singleLine = true,
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                    modifier = Modifier.fillMaxWidth()
                )
                Spacer(Modifier.height(12.dp))
                Text(
                    "Preset rapidi",
                    style = MaterialTheme.typography.labelLarge,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Spacer(Modifier.height(6.dp))
                Row(
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                    modifier = Modifier.horizontalScroll(rememberScrollState())
                ) {
                    listOf(0, 1, 2, 3, 5, 10).forEach { id ->
                        AssistChip(
                            onClick = { markerInput = id.toString() },
                            label = { Text("#$id") },
                            colors = AssistChipDefaults.assistChipColors(
                                containerColor = MaterialTheme.colorScheme.surfaceVariant
                            )
                        )
                    }
                }
            }
        }

        Spacer(Modifier.height(12.dp))

        ElevatedCard(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(20.dp)
        ) {
            Column(Modifier.padding(18.dp)) {
                SectionTitle("Quantità")
                Spacer(Modifier.height(8.dp))
                Row(
                    verticalAlignment = Alignment.Bottom,
                    horizontalArrangement = Arrangement.Center,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text(
                        text = ml.toInt().toString(),
                        fontSize = 56.sp,
                        fontWeight = FontWeight.SemiBold,
                        color = MaterialTheme.colorScheme.primary
                    )
                    Spacer(Modifier.width(6.dp))
                    Text(
                        text = "ml",
                        fontSize = 20.sp,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        modifier = Modifier.padding(bottom = 12.dp)
                    )
                }
                Slider(
                    value = ml,
                    onValueChange = { ml = (it / 10f).toInt() * 10f },
                    valueRange = 10f..500f,
                    steps = 48,
                    colors = SliderDefaults.colors(
                        thumbColor = MaterialTheme.colorScheme.primary,
                        activeTrackColor = MaterialTheme.colorScheme.primary
                    )
                )
            }
        }

        Spacer(Modifier.height(16.dp))

        Button(
            onClick = {
                val id = markerInput.toIntOrNull() ?: return@Button
                onFindAndPour(id, ml.toInt())
            },
            enabled = isConnected && !isBusy && markerInput.toIntOrNull() != null,
            modifier = Modifier
                .fillMaxWidth()
                .height(60.dp),
            shape = RoundedCornerShape(18.dp),
            colors = ButtonDefaults.buttonColors(
                containerColor = MaterialTheme.colorScheme.primary,
                contentColor = MaterialTheme.colorScheme.onPrimary
            )
        ) {
            if (isBusy) {
                CircularProgressIndicator(
                    modifier = Modifier.size(22.dp),
                    strokeWidth = 2.5.dp,
                    color = MaterialTheme.colorScheme.onPrimary
                )
                Spacer(Modifier.width(10.dp))
                Text(pourStatus.message ?: "In corso…", fontWeight = FontWeight.SemiBold)
            } else {
                Icon(Icons.Rounded.LocalDrink, contentDescription = null)
                Spacer(Modifier.width(10.dp))
                Text("Trova e Versa", fontWeight = FontWeight.SemiBold, fontSize = 17.sp)
            }
        }

        Spacer(Modifier.height(16.dp))

        AnimatedVisibility(
            visible = lastAruco != null || pourStatus.phase != PourPhase.Idle,
            enter = fadeIn(),
            exit = fadeOut()
        ) {
            ResultCard(lastAruco = lastAruco, pourStatus = pourStatus)
        }
    }
}

@Composable
private fun HeaderBlock() {
    Column(modifier = Modifier.padding(vertical = 12.dp)) {
        Text(
            text = "Versa",
            style = MaterialTheme.typography.displayLarge,
            color = MaterialTheme.colorScheme.onBackground
        )
        Text(
            text = "Seleziona il marker ArUco e la quantità da erogare",
            style = MaterialTheme.typography.bodyLarge,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}

@Composable
private fun SectionTitle(text: String) {
    Text(
        text = text,
        style = MaterialTheme.typography.titleLarge,
        color = MaterialTheme.colorScheme.onSurface
    )
}

@Composable
private fun ResultCard(lastAruco: InboundMessage.ArucoFound?, pourStatus: PourStatus) {
    ElevatedCard(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(20.dp)
    ) {
        Column(Modifier.padding(18.dp)) {
            SectionTitle("Esito")
            Spacer(Modifier.height(12.dp))
            if (lastAruco != null) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    MetricBlock(
                        icon = Icons.Rounded.MyLocation,
                        label = "Marker",
                        value = "#${lastAruco.markerId}"
                    )
                    MetricBlock(
                        icon = Icons.Rounded.LocalDrink,
                        label = "Distanza",
                        value = "${"%.1f".format(lastAruco.distanceCm)} cm"
                    )
                    MetricBlock(
                        icon = Icons.Rounded.Rotate90DegreesCcw,
                        label = "Angolo",
                        value = "${"%.1f".format(lastAruco.angleDeg)}°"
                    )
                }
                Spacer(Modifier.height(16.dp))
            }
            Crossfade(targetState = pourStatus.phase, label = "phase") { phase ->
                when (phase) {
                    PourPhase.Idle -> Text(
                        "In attesa di un comando",
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    PourPhase.Searching, PourPhase.Pouring -> StatusRow(
                        color = MaterialTheme.colorScheme.tertiary,
                        text = pourStatus.message ?: "In corso…"
                    )
                    PourPhase.Complete -> StatusRow(
                        color = SuccessGreen,
                        icon = Icons.Rounded.CheckCircle,
                        text = pourStatus.message ?: "Completato"
                    )
                    PourPhase.Failed -> StatusRow(
                        color = DangerRed,
                        icon = Icons.Rounded.ErrorOutline,
                        text = pourStatus.message ?: "Errore"
                    )
                }
            }
        }
    }
}

@Composable
private fun StatusRow(
    color: Color,
    icon: androidx.compose.ui.graphics.vector.ImageVector? = null,
    text: String
) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        if (icon != null) {
            Icon(icon, contentDescription = null, tint = color)
        } else {
            CircularProgressIndicator(
                modifier = Modifier.size(16.dp),
                strokeWidth = 2.dp,
                color = color
            )
        }
        Spacer(Modifier.width(8.dp))
        Text(text, color = color, fontWeight = FontWeight.Medium)
    }
}

@Composable
private fun MetricBlock(
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    label: String,
    value: String
) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Box(
            modifier = Modifier
                .size(40.dp)
                .clip(CircleShape)
                .background(
                    Brush.radialGradient(
                        listOf(
                            MaterialTheme.colorScheme.primary.copy(alpha = 0.25f),
                            Color.Transparent
                        )
                    )
                ),
            contentAlignment = Alignment.Center
        ) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.primary
            )
        }
        Spacer(Modifier.height(6.dp))
        Text(value, fontWeight = FontWeight.SemiBold)
        Text(
            label,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}
