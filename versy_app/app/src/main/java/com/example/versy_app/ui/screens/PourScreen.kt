package com.example.versy_app.ui.screens

import androidx.compose.animation.Crossfade
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.clickable
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
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.Add
import androidx.compose.material.icons.rounded.CheckCircle
import androidx.compose.material.icons.rounded.ErrorOutline
import androidx.compose.material.icons.rounded.LocalBar
import androidx.compose.material.icons.rounded.MyLocation
import androidx.compose.material.icons.rounded.Straighten
import androidx.compose.material.icons.rounded.Rotate90DegreesCcw
import androidx.compose.material.icons.rounded.WaterDrop
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.AssistChip
import androidx.compose.material3.AssistChipDefaults
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ElevatedCard
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Slider
import androidx.compose.material3.SliderDefaults
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.rememberModalBottomSheetState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.versy_app.data.ConnectionState
import com.example.versy_app.data.InboundMessage
import com.example.versy_app.ui.components.ArucoMarkerTile
import com.example.versy_app.ui.theme.VersyColors
import com.example.versy_app.viewmodel.PourPhase
import com.example.versy_app.viewmodel.PourStatus

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PourScreen(
    connectionState: ConnectionState,
    lastAruco: InboundMessage.ArucoFound?,
    pourStatus: PourStatus,
    onFindAndPour: (markerId: Int, ml: Int) -> Unit,
    onOpenSettings: () -> Unit,
    onNavigateToJoystick: () -> Unit,
    modifier: Modifier = Modifier
) {
    var selectedId by remember { mutableStateOf<Int?>(null) }
    var ml by remember { mutableFloatStateOf(100f) }
    var showConfirm by remember { mutableStateOf(false) }

    val isConnected = connectionState == ConnectionState.Connected
    val isBusy = pourStatus.phase == PourPhase.Searching || pourStatus.phase == PourPhase.Pouring

    Box(modifier = modifier.fillMaxSize()) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(horizontal = 16.dp)
                .padding(top = 4.dp, bottom = 96.dp)
        ) {
            SummaryHeader(ml = ml.toInt(), selectedId = selectedId)

            Spacer(Modifier.height(12.dp))

            QuantityCard(
                ml = ml,
                onMlChange = { ml = it }
            )

            Spacer(Modifier.height(14.dp))

            Text(
                text = "MARKER",
                style = MaterialTheme.typography.labelLarge,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                fontWeight = FontWeight.SemiBold
            )
            Spacer(Modifier.height(8.dp))

            MarkerGrid(
                selectedId = selectedId,
                onSelect = { selectedId = it },
                onCustom = { selectedId = it }
            )
        }

        Surface(
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .fillMaxWidth(),
            color = MaterialTheme.colorScheme.background.copy(alpha = 0.92f)
        ) {
            Button(
                onClick = { if (selectedId != null) showConfirm = true },
                enabled = isConnected && !isBusy && selectedId != null,
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp, vertical = 14.dp)
                    .height(60.dp),
                shape = RoundedCornerShape(20.dp),
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
                    Icon(Icons.Rounded.LocalBar, contentDescription = null)
                    Spacer(Modifier.width(10.dp))
                    Text(
                        text = if (selectedId != null) "VERSA ${ml.toInt()} ml" else "SELEZIONA UN MARKER",
                        fontWeight = FontWeight.SemiBold,
                        fontSize = 17.sp
                    )
                }
            }
        }
    }

    if (showConfirm && selectedId != null) {
        ConfirmPourSheet(
            markerId = selectedId!!,
            ml = ml.toInt(),
            onConfirm = {
                showConfirm = false
                onFindAndPour(selectedId!!, ml.toInt())
            },
            onDismiss = { showConfirm = false }
        )
    }

    if (!showConfirm && pourStatus.phase != PourPhase.Idle) {
        PourProgressSheet(
            pourStatus = pourStatus,
            lastAruco = lastAruco
        )
    }
}

@Composable
private fun SummaryHeader(ml: Int, selectedId: Int?) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 12.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.Bottom
    ) {
        Column {
            Text(
                text = "Versamento",
                style = MaterialTheme.typography.labelLarge,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            Text(
                text = "$ml ml",
                style = MaterialTheme.typography.displaySmall,
                fontWeight = FontWeight.SemiBold,
                color = MaterialTheme.colorScheme.primary
            )
        }
        Column(horizontalAlignment = Alignment.End) {
            Text(
                text = "Target",
                style = MaterialTheme.typography.labelLarge,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            Text(
                text = selectedId?.let { "#$it" } ?: "—",
                style = MaterialTheme.typography.displaySmall,
                fontWeight = FontWeight.SemiBold,
                color = MaterialTheme.colorScheme.onSurface
            )
        }
    }
}

@Composable
private fun QuantityCard(ml: Float, onMlChange: (Float) -> Unit) {
    ElevatedCard(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(20.dp)
    ) {
        Column(
            modifier = Modifier.padding(horizontal = 18.dp, vertical = 14.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            Text(
                text = "QUANTITÀ",
                style = MaterialTheme.typography.labelLarge,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                fontWeight = FontWeight.SemiBold
            )
            Slider(
                value = ml,
                onValueChange = { onMlChange((it / 10f).toInt() * 10f) },
                valueRange = 10f..500f,
                steps = 48,
                colors = SliderDefaults.colors(
                    thumbColor = MaterialTheme.colorScheme.primary,
                    activeTrackColor = MaterialTheme.colorScheme.primary
                )
            )
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                listOf(50, 100, 200, 500).forEach { v ->
                    val selected = ml.toInt() == v
                    AssistChip(
                        onClick = { onMlChange(v.toFloat()) },
                        label = { Text("$v ml") },
                        colors = AssistChipDefaults.assistChipColors(
                            containerColor = if (selected)
                                MaterialTheme.colorScheme.primaryContainer
                            else
                                MaterialTheme.colorScheme.surfaceVariant,
                            labelColor = if (selected)
                                MaterialTheme.colorScheme.onPrimaryContainer
                            else
                                MaterialTheme.colorScheme.onSurface
                        )
                    )
                }
            }
        }
    }
}

@Composable
private fun MarkerGrid(
    selectedId: Int?,
    onSelect: (Int) -> Unit,
    onCustom: (Int) -> Unit,
    presetIds: List<Int> = (0..11).toList()
) {
    var showCustom by remember { mutableStateOf(false) }

    LazyVerticalGrid(
        columns = GridCells.Fixed(4),
        verticalArrangement = Arrangement.spacedBy(10.dp),
        horizontalArrangement = Arrangement.spacedBy(10.dp),
        contentPadding = PaddingValues(0.dp),
        modifier = Modifier
            .fillMaxWidth()
            .height(340.dp)
    ) {
        items(presetIds, key = { "p-$it" }) { id ->
            ArucoMarkerTile(
                id = id,
                selected = selectedId == id,
                onClick = { onSelect(id) }
            )
        }
        items(listOf("custom"), key = { it }) {
            CustomTile(
                selected = selectedId != null && selectedId !in presetIds,
                customLabel = if (selectedId != null && selectedId !in presetIds) "#$selectedId" else null,
                onClick = { showCustom = true }
            )
        }
    }

    if (showCustom) {
        CustomIdDialog(
            initial = selectedId?.takeIf { it !in presetIds }?.toString().orEmpty(),
            onConfirm = {
                onCustom(it)
                showCustom = false
            },
            onDismiss = { showCustom = false }
        )
    }
}

@Composable
private fun CustomTile(
    selected: Boolean,
    customLabel: String?,
    onClick: () -> Unit
) {
    val borderColor = if (selected) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.outline
    val containerColor = if (selected)
        MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.35f)
    else
        MaterialTheme.colorScheme.surfaceVariant

    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .height(92.dp)
            .clickable(onClick = onClick),
        shape = RoundedCornerShape(18.dp),
        color = containerColor,
        border = BorderStroke(if (selected) 2.dp else 1.dp, borderColor)
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(8.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Icon(
                imageVector = Icons.Rounded.Add,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.primary
            )
            Spacer(Modifier.height(4.dp))
            Text(
                text = customLabel ?: "Custom",
                style = MaterialTheme.typography.labelLarge,
                fontWeight = FontWeight.SemiBold,
                color = MaterialTheme.colorScheme.onSurface
            )
        }
    }
}

@Composable
private fun CustomIdDialog(
    initial: String,
    onConfirm: (Int) -> Unit,
    onDismiss: () -> Unit
) {
    var value by remember { mutableStateOf(initial) }
    val parsed = value.toIntOrNull()
    val valid = parsed != null && parsed in 0..999

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("ID marker personalizzato") },
        text = {
            Column {
                Text(
                    "Inserisci un ID tra 0 e 999.",
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    style = MaterialTheme.typography.bodyMedium
                )
                Spacer(Modifier.height(12.dp))
                OutlinedTextField(
                    value = value,
                    onValueChange = { v -> value = v.filter { it.isDigit() }.take(3) },
                    singleLine = true,
                    label = { Text("ID") },
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number)
                )
            }
        },
        confirmButton = {
            TextButton(
                onClick = { if (valid) onConfirm(parsed!!) },
                enabled = valid
            ) { Text("Seleziona") }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) { Text("Annulla") }
        }
    )
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun ConfirmPourSheet(
    markerId: Int,
    ml: Int,
    onConfirm: () -> Unit,
    onDismiss: () -> Unit
) {
    val sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true)
    ModalBottomSheet(
        onDismissRequest = onDismiss,
        sheetState = sheetState,
        containerColor = MaterialTheme.colorScheme.surface,
        shape = RoundedCornerShape(topStart = 28.dp, topEnd = 28.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 24.dp)
                .padding(bottom = 32.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp)
        ) {
            Text(
                text = "Conferma erogazione",
                style = MaterialTheme.typography.titleLarge,
                fontWeight = FontWeight.SemiBold
            )
            Text(
                text = "Verrà cercato il marker #$markerId e poi erogati $ml ml.",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                OutlinedButton(
                    onClick = onDismiss,
                    modifier = Modifier.weight(1f).height(52.dp),
                    shape = RoundedCornerShape(16.dp)
                ) { Text("Annulla") }
                Button(
                    onClick = onConfirm,
                    modifier = Modifier.weight(1.4f).height(52.dp),
                    shape = RoundedCornerShape(16.dp)
                ) {
                    Icon(Icons.Rounded.LocalBar, contentDescription = null)
                    Spacer(Modifier.width(8.dp))
                    Text("Versa", fontWeight = FontWeight.SemiBold)
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun PourProgressSheet(
    pourStatus: PourStatus,
    lastAruco: InboundMessage.ArucoFound?
) {
    val sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true)
    ModalBottomSheet(
        onDismissRequest = { /* non-dismissable while running */ },
        sheetState = sheetState,
        containerColor = MaterialTheme.colorScheme.surface,
        shape = RoundedCornerShape(topStart = 28.dp, topEnd = 28.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 24.dp)
                .padding(bottom = 32.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp)
        ) {
            Crossfade(targetState = pourStatus.phase, label = "phase") { phase ->
                Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    when (phase) {
                        PourPhase.Idle -> Text("In attesa", color = MaterialTheme.colorScheme.onSurfaceVariant)
                        PourPhase.Searching -> StatusHeader(
                            title = "Cerco il marker…",
                            message = pourStatus.message ?: "",
                            color = MaterialTheme.colorScheme.tertiary,
                            spinner = true
                        )
                        PourPhase.Pouring -> StatusHeader(
                            title = "Sto versando…",
                            message = pourStatus.message ?: "",
                            color = MaterialTheme.colorScheme.tertiary,
                            spinner = true
                        )
                        PourPhase.Complete -> StatusHeader(
                            title = "Erogazione completata",
                            message = pourStatus.message ?: "",
                            color = VersyColors.extended.success,
                            spinner = false,
                            icon = Icons.Rounded.CheckCircle
                        )
                        PourPhase.Failed -> StatusHeader(
                            title = "Errore",
                            message = pourStatus.message ?: "",
                            color = MaterialTheme.colorScheme.error,
                            spinner = false,
                            icon = Icons.Rounded.ErrorOutline
                        )
                    }
                    if (lastAruco != null) {
                        MarkerMetricsRow(lastAruco)
                    }
                }
            }
        }
    }
}

@Composable
private fun StatusHeader(
    title: String,
    message: String,
    color: Color,
    spinner: Boolean,
    icon: androidx.compose.ui.graphics.vector.ImageVector? = null
) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        if (spinner) {
            CircularProgressIndicator(
                modifier = Modifier.size(20.dp),
                strokeWidth = 2.5.dp,
                color = color
            )
        } else if (icon != null) {
            Icon(icon, contentDescription = null, tint = color, modifier = Modifier.size(24.dp))
        }
        Spacer(Modifier.width(12.dp))
        Column {
            Text(title, fontWeight = FontWeight.SemiBold, color = color)
            if (message.isNotEmpty()) {
                Text(message, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
        }
    }
}

@Composable
private fun MarkerMetricsRow(lastAruco: InboundMessage.ArucoFound) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Metric(icon = Icons.Rounded.MyLocation, label = "Marker", value = "#${lastAruco.markerId}")
        Metric(icon = Icons.Rounded.Straighten, label = "Distanza", value = "${"%.1f".format(lastAruco.distanceCm)} cm")
        Metric(icon = Icons.Rounded.Rotate90DegreesCcw, label = "Angolo", value = "${"%.1f".format(lastAruco.angleDeg)}°")
    }
}

@Composable
private fun Metric(
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    label: String,
    value: String
) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Icon(icon, contentDescription = null, tint = MaterialTheme.colorScheme.primary)
        Spacer(Modifier.height(4.dp))
        Text(value, fontWeight = FontWeight.SemiBold)
        Text(label, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}
