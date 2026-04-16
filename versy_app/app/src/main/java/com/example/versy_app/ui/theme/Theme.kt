package com.example.versy_app.ui.theme

import android.app.Activity
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalView
import androidx.core.view.WindowCompat

private val VersyDarkColors = darkColorScheme(
    primary = PrimaryTeal,
    onPrimary = Color(0xFF00332D),
    primaryContainer = PrimaryTealDim,
    onPrimaryContainer = Color(0xFFE6FFFA),
    secondary = SecondaryMagenta,
    onSecondary = Color(0xFF3D0018),
    tertiary = AccentAmber,
    onTertiary = Color(0xFF3D2A00),
    background = BackgroundDark,
    onBackground = TextPrimary,
    surface = SurfaceDark,
    onSurface = TextPrimary,
    surfaceVariant = SurfaceElevated,
    onSurfaceVariant = TextSecondary,
    outline = OutlineDark,
    error = DangerRed,
    onError = Color.White
)

@Composable
fun VersyTheme(
    content: @Composable () -> Unit
) {
    val colorScheme = VersyDarkColors
    val view = LocalView.current
    if (!view.isInEditMode) {
        SideEffect {
            val window = (view.context as Activity).window
            window.statusBarColor = Color.Transparent.toArgb()
            window.navigationBarColor = BackgroundDark.toArgb()
            WindowCompat.getInsetsController(window, view).apply {
                isAppearanceLightStatusBars = false
                isAppearanceLightNavigationBars = false
            }
        }
    }
    MaterialTheme(
        colorScheme = colorScheme,
        typography = VersyTypography,
        content = content
    )
}
