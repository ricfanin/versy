package com.example.versy_app.ui.screens

import androidx.compose.animation.Crossfade
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.RowScope
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.Add
import androidx.compose.material.icons.rounded.CheckCircle
import androidx.compose.material.icons.rounded.ErrorOutline
import androidx.compose.material.icons.rounded.LocalBar
import androidx.compose.material.icons.rounded.Stop
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
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.versy_app.data.ArucoMarkers
import com.example.versy_app.data.ConnectionState
import com.example.versy_app.data.InboundMessage
import com.example.versy_app.ui.components.ArucoMarkerTile
import com.example.versy_app.ui.components.RobotStatusPanel
import com.example.versy_app.ui.theme.VersyColors
import com.example.versy_app.viewmodel.PourPhase
import com.example.versy_app.viewmodel.PourStatus
import com.example.versy_app.viewmodel.isActive

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PourScreen(
    connectionState: ConnectionState,
    robotStatus: InboundMessage.RobotStatus?,
    username: String,
    pourStatus: PourStatus,
    customMarkers: List<Int>,
    onRequestPour: (markerId: Int, ml: Int) -> Unit,
    onStopPour: () -> Unit,
    onResetPour: () -> Unit,
    onAddCustomMarker: (Int) -> Unit,
    onRemoveCustomMarker: (Int) -> Unit,
    onOpenSettings: () -> Unit,
    onNavigateToJoystick: () -> Unit,
    modifier: Modifier = Modifier
) {
    var selectedId by rememberSaveable { mutableStateOf<Int?>(null) }
    var ml by rememberSaveable { mutableFloatStateOf(100f) }
    var showConfirm by remember { mutableStateOf(false) }

    val isConnected = connectionState == ConnectionState.Connected
    val isBusy = pourStatus.phase.isActive

    Box(modifier = modifier.fillMaxSize()) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 16.dp)
                .padding(top = 4.dp, bottom = 96.dp)
        ) {
            RobotStatusPanel(status = robotStatus, username = username)

            Spacer(Modifier.height(12.dp))

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
                customMarkers = customMarkers,
                onSelect = { selectedId = it },
                onAddCustomMarker = { id ->
                    onAddCustomMarker(id)
                    selectedId = id
                },
                onRemoveCustomMarker = { id ->
                    onRemoveCustomMarker(id)
                    if (selectedId == id) selectedId = null
                }
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
                onRequestPour(selectedId!!, ml.toInt())
            },
            onDismiss = { showConfirm = false }
        )
    }

    if (!showConfirm && pourStatus.phase != PourPhase.Idle) {
        PourProgressSheet(
            pourStatus = pourStatus,
            onStop = onStopPour,
            onDismiss = onResetPour
        )
    }
}

@Composable
private fun SummaryHeader(ml: Int, selectedId: Int?) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 4.dp),
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
    customMarkers: List<Int>,
    onSelect: (Int) -> Unit,
    onAddCustomMarker: (Int) -> Unit,
    onRemoveCustomMarker: (Int) -> Unit,
    presetIds: List<Int> = (0..11).toList(),
    columns: Int = 4
) {
    var showAdd by remember { mutableStateOf(false) }
    var removeTarget by remember { mutableStateOf<Int?>(null) }

    val cells: List<@Composable RowScope.() -> Unit> = buildList {
        presetIds.forEach { id ->
            add {
                ArucoMarkerTile(
                    id = id,
                    selected = selectedId == id,
                    onClick = { onSelect(id) },
                    modifier = Modifier.weight(1f)
                )
            }
        }
        customMarkers.forEach { id ->
            add {
                ArucoMarkerTile(
                    id = id,
                    selected = selectedId == id,
                    onClick = { onSelect(id) },
                    onLongClick = { removeTarget = id },
                    modifier = Modifier.weight(1f)
                )
            }
        }
        add {
            AddMarkerTile(
                onClick = { showAdd = true },
                modifier = Modifier.weight(1f)
            )
        }
    }

    Column(
        modifier = Modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        cells.chunked(columns).forEach { rowCells ->
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                rowCells.forEach { cell -> cell() }
                repeat(columns - rowCells.size) { Spacer(Modifier.weight(1f)) }
            }
        }
    }

    if (showAdd) {
        CustomIdDialog(
            existing = presetIds.toSet() + customMarkers.toSet(),
            onConfirm = {
                onAddCustomMarker(it)
                showAdd = false
            },
            onDismiss = { showAdd = false }
        )
    }

    removeTarget?.let { id ->
        RemoveMarkerDialog(
            id = id,
            onConfirm = {
                onRemoveCustomMarker(id)
                removeTarget = null
            },
            onDismiss = { removeTarget = null }
        )
    }
}

@Composable
private fun AddMarkerTile(
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier
            .clip(RoundedCornerShape(18.dp))
            .clickable(onClick = onClick),
        shape = RoundedCornerShape(18.dp),
        color = MaterialTheme.colorScheme.surfaceVariant,
        border = BorderStroke(1.dp, MaterialTheme.colorScheme.outline)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(8.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .aspectRatio(1f)
                    .clip(RoundedCornerShape(6.dp))
                    .background(MaterialTheme.colorScheme.surface),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = Icons.Rounded.Add,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.primary,
                    modifier = Modifier.size(28.dp)
                )
            }
            Spacer(Modifier.height(6.dp))
            Text(
                text = "Aggiungi",
                style = MaterialTheme.typography.labelLarge,
                fontWeight = FontWeight.SemiBold,
                color = MaterialTheme.colorScheme.onSurface
            )
        }
    }
}

@Composable
private fun CustomIdDialog(
    existing: Set<Int>,
    onConfirm: (Int) -> Unit,
    onDismiss: () -> Unit
) {
    var value by remember { mutableStateOf("") }
    val parsed = value.toIntOrNull()
    val inRange = parsed != null && parsed in ArucoMarkers.idRange
    val duplicate = parsed != null && parsed in existing
    val valid = inRange && !duplicate

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Aggiungi marker") },
        text = {
            Column {
                Text(
                    "Inserisci un ID tra ${ArucoMarkers.idRange.first} e ${ArucoMarkers.idRange.last} " +
                        "(dizionario DICT_4X4_250).",
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    style = MaterialTheme.typography.bodyMedium
                )
                Spacer(Modifier.height(12.dp))
                OutlinedTextField(
                    value = value,
                    onValueChange = { v -> value = v.filter { it.isDigit() }.take(3) },
                    singleLine = true,
                    isError = parsed != null && !valid,
                    label = { Text("ID") },
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number)
                )
                if (duplicate) {
                    Spacer(Modifier.height(6.dp))
                    Text(
                        text = "Marker #$parsed già presente.",
                        color = MaterialTheme.colorScheme.error,
                        style = MaterialTheme.typography.bodySmall
                    )
                }
            }
        },
        confirmButton = {
            TextButton(
                onClick = { if (valid) onConfirm(parsed!!) },
                enabled = valid
            ) { Text("Aggiungi") }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) { Text("Annulla") }
        }
    )
}

@Composable
private fun RemoveMarkerDialog(
    id: Int,
    onConfirm: () -> Unit,
    onDismiss: () -> Unit
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Rimuovere il marker?") },
        text = {
            Text(
                text = "Il marker #$id verrà rimosso dalla lista.",
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                style = MaterialTheme.typography.bodyMedium
            )
        },
        confirmButton = {
            TextButton(
                onClick = onConfirm,
                colors = ButtonDefaults.textButtonColors(
                    contentColor = MaterialTheme.colorScheme.error
                )
            ) { Text("Rimuovi") }
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
                text = "Il robot cercherà il marker #$markerId e avvierà il versamento. " +
                    "La richiesta viene accodata se è già in corso un altro lavoro.",
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
    onStop: () -> Unit,
    onDismiss: () -> Unit
) {
    val sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true)
    val terminal = pourStatus.phase == PourPhase.Done || pourStatus.phase == PourPhase.Failed
    ModalBottomSheet(
        onDismissRequest = { if (terminal) onDismiss() },
        sheetState = sheetState,
        containerColor = MaterialTheme.colorScheme.surface,
        shape = RoundedCornerShape(topStart = 28.dp, topEnd = 28.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 24.dp)
                .padding(bottom = 32.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            Crossfade(targetState = pourStatus.phase, label = "phase") { phase ->
                when (phase) {
                    PourPhase.Idle -> Text("In attesa", color = MaterialTheme.colorScheme.onSurfaceVariant)
                    PourPhase.Queued -> StatusHeader(
                        title = "In coda",
                        message = pourStatus.message ?: "",
                        color = MaterialTheme.colorScheme.tertiary,
                        spinner = true
                    )
                    PourPhase.Searching -> StatusHeader(
                        title = "Cerco il marker…",
                        message = pourStatus.message ?: "",
                        color = MaterialTheme.colorScheme.tertiary,
                        spinner = true
                    )
                    PourPhase.Approaching -> StatusHeader(
                        title = "Mi avvicino…",
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
                    PourPhase.Done -> StatusHeader(
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
            }

            if (terminal) {
                Button(
                    onClick = onDismiss,
                    modifier = Modifier.fillMaxWidth().height(52.dp),
                    shape = RoundedCornerShape(16.dp)
                ) { Text("Chiudi", fontWeight = FontWeight.SemiBold) }
            } else {
                OutlinedButton(
                    onClick = onStop,
                    modifier = Modifier.fillMaxWidth().height(52.dp),
                    shape = RoundedCornerShape(16.dp),
                    border = BorderStroke(1.5.dp, MaterialTheme.colorScheme.error),
                    colors = ButtonDefaults.outlinedButtonColors(
                        contentColor = MaterialTheme.colorScheme.error
                    )
                ) {
                    Icon(Icons.Rounded.Stop, contentDescription = null)
                    Spacer(Modifier.width(8.dp))
                    Text("Interrompi", fontWeight = FontWeight.SemiBold)
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
