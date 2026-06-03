package com.example.versy_app.ui.navigation

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.Gamepad
import androidx.compose.material.icons.rounded.LocalDrink
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.NavigationBarItemDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.example.versy_app.data.ConnectionState
import com.example.versy_app.ui.components.MinimalConnectionBar
import com.example.versy_app.ui.components.SettingsBottomSheet
import com.example.versy_app.ui.screens.JoystickScreen
import com.example.versy_app.ui.screens.PourScreen
import com.example.versy_app.viewmodel.AppViewModel

private enum class Route(val path: String, val label: String, val icon: ImageVector) {
    Pour("pour", "Versa", Icons.Rounded.LocalDrink),
    Joystick("joystick", "Pilota", Icons.Rounded.Gamepad)
}

@Composable
fun AppNavigation(
    viewModel: AppViewModel = viewModel()
) {
    val navController = rememberNavController()
    val connectionState by viewModel.connectionState.collectAsStateWithLifecycle()
    val address by viewModel.address.collectAsStateWithLifecycle()
    val username by viewModel.username.collectAsStateWithLifecycle()
    val robotStatus by viewModel.robotStatus.collectAsStateWithLifecycle()
    val pourStatus by viewModel.pourStatus.collectAsStateWithLifecycle()
    val customMarkers by viewModel.customMarkers.collectAsStateWithLifecycle()

    var showSettings by remember { mutableStateOf(false) }

    val currentEntry by navController.currentBackStackEntryAsState()
    val isJoystickRoute = currentEntry?.destination?.route == Route.Joystick.path

    Scaffold(
        containerColor = MaterialTheme.colorScheme.background,
        topBar = {
            if (!isJoystickRoute) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .statusBarsPadding()
                        .padding(horizontal = 16.dp, vertical = 10.dp),
                    horizontalArrangement = Arrangement.Start,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    MinimalConnectionBar(
                        state = connectionState,
                        onClick = { showSettings = true }
                    )
                }
            }
        },
        bottomBar = {
            if (!isJoystickRoute) VersyBottomBar(navController)
        }
    ) { innerPadding ->
        NavHost(
            navController = navController,
            startDestination = Route.Pour.path,
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
        ) {
            composable(Route.Pour.path) {
                PourScreen(
                    connectionState = connectionState,
                    robotStatus = robotStatus,
                    username = username,
                    pourStatus = pourStatus,
                    customMarkers = customMarkers,
                    onRequestPour = viewModel::requestPour,
                    onStopPour = viewModel::stopPour,
                    onResetPour = viewModel::resetPourStatus,
                    onAddCustomMarker = viewModel::addCustomMarker,
                    onRemoveCustomMarker = viewModel::removeCustomMarker,
                    onOpenSettings = { showSettings = true },
                    onNavigateToJoystick = {
                        navController.navigate(Route.Joystick.path) {
                            popUpTo(navController.graph.startDestinationId) { saveState = true }
                            launchSingleTop = true
                            restoreState = true
                        }
                    }
                )
            }
            composable(Route.Joystick.path) {
                JoystickScreen(
                    connectionState = connectionState,
                    onMove = viewModel::sendMove,
                    onStop = viewModel::sendStop,
                    onPourPressStart = viewModel::startManualPour,
                    onPourPressStop = viewModel::stopManualPour,
                    onOpenConnection = { showSettings = true },
                    onBackToPour = {
                        navController.navigate(Route.Pour.path) {
                            popUpTo(navController.graph.startDestinationId) { saveState = true }
                            launchSingleTop = true
                            restoreState = true
                        }
                    }
                )
            }
        }
    }

    if (showSettings) {
        SettingsBottomSheet(
            state = connectionState,
            address = address,
            username = username,
            onAddressChange = viewModel::updateAddress,
            onUsernameChange = viewModel::updateUsername,
            onToggleConnect = {
                if (connectionState == ConnectionState.Connected) viewModel.disconnect()
                else viewModel.connect()
            },
            onDismiss = { showSettings = false }
        )
    }
}

@Composable
private fun VersyBottomBar(navController: NavHostController) {
    val currentEntry by navController.currentBackStackEntryAsState()
    val currentRoute = currentEntry?.destination?.route
    NavigationBar(
        containerColor = MaterialTheme.colorScheme.surface
    ) {
        Route.entries.forEach { route ->
            val selected = currentRoute == route.path
            NavigationBarItem(
                selected = selected,
                onClick = {
                    if (!selected) {
                        navController.navigate(route.path) {
                            popUpTo(navController.graph.startDestinationId) { saveState = true }
                            launchSingleTop = true
                            restoreState = true
                        }
                    }
                },
                icon = { Icon(route.icon, contentDescription = route.label) },
                label = { Text(route.label) },
                colors = NavigationBarItemDefaults.colors(
                    selectedIconColor = MaterialTheme.colorScheme.onPrimaryContainer,
                    selectedTextColor = MaterialTheme.colorScheme.primary,
                    indicatorColor = MaterialTheme.colorScheme.primary.copy(alpha = 0.25f),
                    unselectedIconColor = MaterialTheme.colorScheme.onSurfaceVariant,
                    unselectedTextColor = MaterialTheme.colorScheme.onSurfaceVariant
                )
            )
        }
    }
}
