package com.example.versy_app.ui.screens

import android.app.Activity
import android.content.pm.ActivityInfo
import androidx.compose.animation.animateColorAsState
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.awaitEachGesture
import androidx.compose.foundation.gestures.awaitFirstDown
import androidx.compose.foundation.gestures.waitForUpOrCancellation
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawingPadding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.rounded.ArrowBack
import androidx.compose.material.icons.rounded.LocalBar
import androidx.compose.material.icons.rounded.Stop
import androidx.compose.material3.FilledTonalButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.IconButtonDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.setValue
import androidx.compose.runtime.snapshotFlow
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.versy_app.data.ConnectionState
import com.example.versy_app.ui.components.MinimalConnectionBar
import com.example.versy_app.ui.components.OmniJoystick
import com.example.versy_app.ui.components.YawDial
import kotlinx.coroutines.FlowPreview
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.sample
import kotlin.math.abs

@OptIn(FlowPreview::class)
@Composable
fun JoystickScreen(
    connectionState: ConnectionState,
    onMove: (vx: Float, vy: Float, omega: Float) -> Unit,
    onStop: () -> Unit,
    onPourPressStart: () -> Unit,
    onPourPressStop: () -> Unit,
    onOpenConnection: () -> Unit,
    onBackToPour: () -> Unit,
    modifier: Modifier = Modifier
) {
    ForceLandscape()

    var vx by remember { mutableFloatStateOf(0f) }
    var vy by remember { mutableFloatStateOf(0f) }
    var omega by remember { mutableFloatStateOf(0f) }

    val isConnected = connectionState == ConnectionState.Connected

    LaunchedEffect(isConnected) {
        if (!isConnected) return@LaunchedEffect
        snapshotFlow { Triple(vx, vy, omega) }
            .sample(100)
            .distinctUntilChanged()
            .collect { (x, y, w) ->
                if (abs(x) > 0.001f || abs(y) > 0.001f || abs(w) > 0.001f) {
                    onMove(x, y, w)
                }
            }
    }

    Box(
        modifier = modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
            .safeDrawingPadding()
            .padding(horizontal = 20.dp, vertical = 12.dp)
    ) {
        MinimalConnectionBar(
            state = connectionState,
            onClick = onOpenConnection,
            modifier = Modifier.align(Alignment.TopStart),
            compact = true
        )

        BackToPourButton(
            onClick = onBackToPour,
            modifier = Modifier.align(Alignment.TopCenter)
        )

        StickPanel(
            labelLine1 = "VX %+.2f".format(vx),
            labelLine2 = "VY %+.2f".format(vy),
            alignEnd = false,
            modifier = Modifier.align(Alignment.CenterStart),
            control = {
                OmniJoystick(
                    size = 220.dp,
                    onMove = { nx, ny ->
                        vx = nx
                        vy = ny
                    },
                    onRelease = {
                        vx = 0f
                        vy = 0f
                        if (abs(omega) < 0.001f) onStop()
                    }
                )
            }
        )

        StickPanel(
            labelLine1 = "YAW \u03C9 %+.2f".format(omega),
            labelLine2 = "",
            alignEnd = true,
            modifier = Modifier.align(Alignment.CenterEnd),
            control = {
                YawDial(
                    diameter = 220.dp,
                    onChange = { omega = it },
                    onRelease = {
                        omega = 0f
                        if (abs(vx) < 0.001f && abs(vy) < 0.001f) onStop()
                    }
                )
            }
        )

        ActionButtonStack(
            onPourPressStart = onPourPressStart,
            onPourPressStop = onPourPressStop,
            onStop = {
                vx = 0f; vy = 0f; omega = 0f
                onStop()
            },
            isConnected = isConnected,
            modifier = Modifier.align(Alignment.Center)
        )

        if (!isConnected) {
            Text(
                text = "Connettiti al robot per pilotare",
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                style = MaterialTheme.typography.bodyMedium,
                modifier = Modifier.align(Alignment.BottomCenter)
            )
        }
    }
}

@Composable
private fun ActionButtonStack(
    onPourPressStart: () -> Unit,
    onPourPressStop: () -> Unit,
    onStop: () -> Unit,
    isConnected: Boolean,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier,
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(20.dp)
    ) {
        PushToPourButton(
            onPressStart = onPourPressStart,
            onPressStop = onPourPressStop,
            isConnected = isConnected
        )
        IconButton(
            onClick = onStop,
            modifier = Modifier
                .size(88.dp)
                .clip(CircleShape),
            colors = IconButtonDefaults.iconButtonColors(
                containerColor = MaterialTheme.colorScheme.error,
                contentColor = MaterialTheme.colorScheme.onError
            )
        ) {
            Icon(
                imageVector = Icons.Rounded.Stop,
                contentDescription = "Stop emergenza",
                modifier = Modifier.size(40.dp)
            )
        }
    }
}

/**
 * Pulsante "tieni premuto per versare" (push-to-pour): nessuna sheet, azione immediata.
 *
 * Alla pressione invoca [onPressStart], al rilascio (o all'annullamento del gesto, es. dito
 * che esce dall'area) invoca [onPressStop]. Un [DisposableEffect] garantisce lo stop anche
 * se la schermata viene lasciata mentre il pulsante è premuto, così il comando di stop
 * raggiunge sempre il robot.
 */
@Composable
private fun PushToPourButton(
    onPressStart: () -> Unit,
    onPressStop: () -> Unit,
    isConnected: Boolean,
    modifier: Modifier = Modifier
) {
    var holding by remember { mutableStateOf(false) }

    // Letture aggiornate per il DisposableEffect, che cattura i valori al primo composing.
    val holdingState = rememberUpdatedState(holding)
    val onPressStopState = rememberUpdatedState(onPressStop)
    DisposableEffect(Unit) {
        onDispose {
            if (holdingState.value) onPressStopState.value()
        }
    }

    // Se ci si disconnette mentre è premuto, chiudi il gesto e notifica lo stop.
    LaunchedEffect(isConnected) {
        if (!isConnected && holding) {
            holding = false
            onPressStop()
        }
    }

    val containerColor by animateColorAsState(
        targetValue = when {
            !isConnected -> MaterialTheme.colorScheme.primary.copy(alpha = 0.3f)
            holding -> MaterialTheme.colorScheme.tertiary
            else -> MaterialTheme.colorScheme.primary
        },
        label = "pourBtnColor"
    )

    Box(
        modifier = modifier
            .size(88.dp)
            .clip(CircleShape)
            .background(containerColor)
            .semantics { contentDescription = "Tieni premuto per versare" }
            .pointerInput(isConnected) {
                if (!isConnected) return@pointerInput
                awaitEachGesture {
                    awaitFirstDown(requireUnconsumed = false)
                    holding = true
                    onPressStart()
                    // null = gesto annullato (dito fuori area / cancel): trattato come rilascio.
                    waitForUpOrCancellation()
                    holding = false
                    onPressStop()
                }
            },
        contentAlignment = Alignment.Center
    ) {
        Icon(
            imageVector = Icons.Rounded.LocalBar,
            contentDescription = null,
            tint = if (holding)
                MaterialTheme.colorScheme.onTertiary
            else
                MaterialTheme.colorScheme.onPrimary,
            modifier = Modifier.size(40.dp)
        )
    }
}

@Composable
private fun BackToPourButton(onClick: () -> Unit, modifier: Modifier = Modifier) {
    FilledTonalButton(
        onClick = onClick,
        modifier = modifier.height(44.dp),
        shape = RoundedCornerShape(22.dp)
    ) {
        Icon(
            imageVector = Icons.AutoMirrored.Rounded.ArrowBack,
            contentDescription = null,
            modifier = Modifier.size(20.dp)
        )
        Spacer(Modifier.width(8.dp))
        Text(
            text = "Indietro",
            style = MaterialTheme.typography.labelLarge,
            fontWeight = FontWeight.SemiBold,
            fontSize = 14.sp
        )
    }
}

@Composable
private fun StickPanel(
    labelLine1: String,
    labelLine2: String,
    alignEnd: Boolean,
    modifier: Modifier = Modifier,
    control: @Composable () -> Unit
) {
    Column(
        modifier = modifier,
        horizontalAlignment = if (alignEnd) Alignment.End else Alignment.Start,
        verticalArrangement = Arrangement.spacedBy(6.dp)
    ) {
        Row {
            Text(
                text = labelLine1,
                style = MaterialTheme.typography.labelLarge,
                fontWeight = FontWeight.SemiBold,
                color = MaterialTheme.colorScheme.primary,
                fontSize = 13.sp
            )
            if (labelLine2.isNotEmpty()) {
                Spacer(Modifier.width(12.dp))
                Text(
                    text = labelLine2,
                    style = MaterialTheme.typography.labelLarge,
                    fontWeight = FontWeight.SemiBold,
                    color = MaterialTheme.colorScheme.primary,
                    fontSize = 13.sp
                )
            }
        }
        control()
    }
}

@Composable
private fun ForceLandscape() {
    val context = LocalContext.current
    DisposableEffect(Unit) {
        val activity = context as? Activity
        val previous = activity?.requestedOrientation
        activity?.requestedOrientation = ActivityInfo.SCREEN_ORIENTATION_SENSOR_LANDSCAPE
        onDispose {
            activity?.requestedOrientation = previous ?: ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED
        }
    }
}
