package com.example.versy_app.ui.components

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.LinkOff
import androidx.compose.material.icons.rounded.Wifi
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.rememberModalBottomSheetState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.example.versy_app.data.ConnectionState

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsBottomSheet(
    state: ConnectionState,
    address: String,
    onAddressChange: (String) -> Unit,
    onToggleConnect: () -> Unit,
    onDismiss: () -> Unit
) {
    val sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true)
    var editing by remember { mutableStateOf(address) }

    ModalBottomSheet(
        onDismissRequest = onDismiss,
        sheetState = sheetState,
        containerColor = MaterialTheme.colorScheme.surface,
        shape = RoundedCornerShape(topStart = 28.dp, topEnd = 28.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(PaddingValues(horizontal = 24.dp, vertical = 8.dp))
                .padding(bottom = 32.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp)
        ) {
            Text(
                text = "Connessione",
                style = MaterialTheme.typography.titleLarge,
                fontWeight = FontWeight.SemiBold
            )
            StatusLine(state)

            OutlinedTextField(
                value = editing,
                onValueChange = { editing = it },
                label = { Text("Indirizzo IP:porta") },
                singleLine = true,
                modifier = Modifier.fillMaxWidth()
            )

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                val isConnected = state == ConnectionState.Connected
                val trimmed = editing.trim()
                val addressChanged = trimmed != address && trimmed.isNotEmpty()

                OutlinedButton(
                    onClick = {
                        if (addressChanged) onAddressChange(trimmed)
                    },
                    enabled = addressChanged,
                    modifier = Modifier.weight(1f).height(52.dp),
                    shape = RoundedCornerShape(16.dp)
                ) {
                    Text("Salva IP")
                }
                Button(
                    onClick = {
                        if (addressChanged) onAddressChange(trimmed)
                        onToggleConnect()
                    },
                    modifier = Modifier.weight(1f).height(52.dp),
                    shape = RoundedCornerShape(16.dp),
                    colors = if (isConnected)
                        ButtonDefaults.buttonColors(
                            containerColor = MaterialTheme.colorScheme.errorContainer,
                            contentColor = MaterialTheme.colorScheme.onErrorContainer
                        )
                    else
                        ButtonDefaults.buttonColors()
                ) {
                    Icon(
                        imageVector = if (isConnected) Icons.Rounded.LinkOff else Icons.Rounded.Wifi,
                        contentDescription = null
                    )
                    Spacer(Modifier.height(0.dp).then(Modifier))
                    Text(
                        text = if (isConnected) "Disconnetti" else "Connetti",
                        fontWeight = FontWeight.SemiBold,
                        modifier = Modifier.padding(start = 6.dp)
                    )
                }
            }
        }
    }
}

@Composable
private fun StatusLine(state: ConnectionState) {
    val (label, color) = when (state) {
        ConnectionState.Connected -> "Collegato al robot" to MaterialTheme.colorScheme.primary
        ConnectionState.Connecting -> "Connessione in corso…" to MaterialTheme.colorScheme.tertiary
        ConnectionState.Disconnected -> "Non collegato" to MaterialTheme.colorScheme.onSurfaceVariant
        is ConnectionState.Error -> "Errore: ${state.reason}" to MaterialTheme.colorScheme.error
    }
    Text(
        text = label,
        style = MaterialTheme.typography.bodyMedium,
        color = color
    )
}
