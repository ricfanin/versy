package com.example.versy_app.ui.components

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.ExpandLess
import androidx.compose.material.icons.rounded.ExpandMore
import androidx.compose.material.icons.rounded.Group
import androidx.compose.material3.ElevatedCard
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.example.versy_app.data.InboundMessage
import com.example.versy_app.data.RobotJob
import com.example.versy_app.data.RobotState

/** Etichetta leggibile per lo stato del robot (niente nomi di classe interni). */
fun RobotState.label(): String = when (this) {
    RobotState.INIT -> "In attesa"
    RobotState.SCAN -> "In ricerca"
    RobotState.MOVING -> "Avvicinamento"
    RobotState.POURING -> "Versamento"
    RobotState.RETREAT -> "Ritorno"
    RobotState.UNKNOWN -> "—"
}

private fun RobotState.color(scheme: androidx.compose.material3.ColorScheme): Color = when (this) {
    RobotState.INIT, RobotState.UNKNOWN -> scheme.onSurfaceVariant
    RobotState.RETREAT -> scheme.tertiary
    else -> scheme.primary
}

/**
 * Pannello che riassume lo stato del robot ricostruito dal robot_status:
 * stato corrente, job in lavorazione, coda (con l'utente corrente evidenziato)
 * e utenti connessi.
 */
@Composable
fun RobotStatusPanel(
    status: InboundMessage.RobotStatus?,
    username: String,
    modifier: Modifier = Modifier
) {
    var usersExpanded by remember { mutableStateOf(false) }

    ElevatedCard(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(20.dp)
    ) {
        Column(
            modifier = Modifier.padding(horizontal = 16.dp, vertical = 14.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "STATO ROBOT",
                    style = MaterialTheme.typography.labelLarge,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    fontWeight = FontWeight.SemiBold
                )
                if (status != null) {
                    val canExpand = status.connectedUsers.isNotEmpty()
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        modifier = Modifier
                            .clip(RoundedCornerShape(8.dp))
                            .then(
                                if (canExpand) Modifier.clickable { usersExpanded = !usersExpanded }
                                else Modifier
                            )
                            .padding(horizontal = 6.dp, vertical = 2.dp)
                    ) {
                        Icon(
                            imageVector = Icons.Rounded.Group,
                            contentDescription = null,
                            tint = MaterialTheme.colorScheme.onSurfaceVariant,
                            modifier = Modifier.size(18.dp)
                        )
                        Spacer(Modifier.width(4.dp))
                        Text(
                            text = "${status.connectedUsers.size}",
                            style = MaterialTheme.typography.labelLarge,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                        if (canExpand) {
                            Spacer(Modifier.width(2.dp))
                            Icon(
                                imageVector = if (usersExpanded) Icons.Rounded.ExpandLess
                                else Icons.Rounded.ExpandMore,
                                contentDescription = if (usersExpanded) "Nascondi utenti connessi"
                                else "Mostra utenti connessi",
                                tint = MaterialTheme.colorScheme.onSurfaceVariant,
                                modifier = Modifier.size(18.dp)
                            )
                        }
                    }
                }
            }

            if (status == null) {
                Text(
                    text = "Non connesso",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                return@Column
            }

            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(
                    modifier = Modifier
                        .size(10.dp)
                        .clip(CircleShape)
                        .background(status.state.color(MaterialTheme.colorScheme))
                )
                Spacer(Modifier.width(8.dp))
                Text(
                    text = status.state.label(),
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.SemiBold,
                    color = status.state.color(MaterialTheme.colorScheme)
                )
                Spacer(Modifier.width(8.dp))
                val current = status.currentJob
                if (current != null) {
                    Text(
                        text = "· ${displayUser(current.username, username)} → #${current.markerId}",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurface
                    )
                } else {
                    Text(
                        text = "· nessun job",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }

            if (status.queue.isNotEmpty()) {
                Text(
                    text = "CODA",
                    style = MaterialTheme.typography.labelMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    fontWeight = FontWeight.SemiBold
                )
                status.queue.forEachIndexed { index, job ->
                    QueueRow(position = index + 1, job = job, myUsername = username)
                }
            }

            AnimatedVisibility(visible = usersExpanded && status.connectedUsers.isNotEmpty()) {
                Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    Text(
                        text = "CONNESSI",
                        style = MaterialTheme.typography.labelMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        fontWeight = FontWeight.SemiBold
                    )
                    status.connectedUsers.forEach { user ->
                        ConnectedUserRow(user = user, myUsername = username)
                    }
                }
            }
        }
    }
}

@Composable
private fun ConnectedUserRow(user: String, myUsername: String) {
    val isMine = user == myUsername
    Row(
        modifier = Modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Box(
            modifier = Modifier
                .size(7.dp)
                .clip(CircleShape)
                .background(
                    if (isMine) MaterialTheme.colorScheme.primary
                    else MaterialTheme.colorScheme.onSurfaceVariant
                )
        )
        Spacer(Modifier.width(10.dp))
        Text(
            text = displayUser(user, myUsername),
            style = MaterialTheme.typography.bodyMedium,
            fontWeight = if (isMine) FontWeight.SemiBold else FontWeight.Normal,
            color = if (isMine) MaterialTheme.colorScheme.primary
            else MaterialTheme.colorScheme.onSurface
        )
    }
}

@Composable
private fun QueueRow(position: Int, job: RobotJob, myUsername: String) {
    val isMine = job.username == myUsername
    Row(
        modifier = Modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Surface(
            shape = CircleShape,
            color = if (isMine) MaterialTheme.colorScheme.primary
            else MaterialTheme.colorScheme.surfaceVariant,
            modifier = Modifier.size(22.dp)
        ) {
            Box(contentAlignment = Alignment.Center) {
                Text(
                    text = "$position",
                    style = MaterialTheme.typography.labelMedium,
                    color = if (isMine) MaterialTheme.colorScheme.onPrimary
                    else MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
        Spacer(Modifier.width(10.dp))
        Text(
            text = displayUser(job.username, myUsername),
            style = MaterialTheme.typography.bodyMedium,
            fontWeight = if (isMine) FontWeight.SemiBold else FontWeight.Normal,
            color = if (isMine) MaterialTheme.colorScheme.primary
            else MaterialTheme.colorScheme.onSurface
        )
        Spacer(Modifier.width(6.dp))
        Text(
            text = "→ #${job.markerId}",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}

private fun displayUser(user: String, myUsername: String): String =
    if (user == myUsername) "$user (tu)" else user
