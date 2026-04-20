package com.example.versy_app.ui.theme

import android.app.Activity
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.Immutable
import androidx.compose.runtime.SideEffect
import androidx.compose.runtime.compositionLocalOf
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalView
import androidx.core.view.WindowCompat

@Immutable
data class ExtendedColors(
    val success: Color,
    val onSuccess: Color,
    val warning: Color,
    val onWarning: Color
)

private val ExtendedColorsDark = ExtendedColors(
    success = SuccessGreenDark,
    onSuccess = Color(0xFF003A1B),
    warning = WarningAmberDark,
    onWarning = Color(0xFF3D2A00)
)

private val ExtendedColorsLight = ExtendedColors(
    success = SuccessGreenLight,
    onSuccess = Color.White,
    warning = WarningAmberLight,
    onWarning = Color.White
)

val LocalExtendedColors = compositionLocalOf { ExtendedColorsDark }

private val VersyDarkColors = darkColorScheme(
    primary = PrimarySkyDark,
    onPrimary = OnPrimaryDark,
    primaryContainer = PrimarySkyDarkDim,
    onPrimaryContainer = Color(0xFFE0F2FE),
    secondary = SecondaryLilacDark,
    onSecondary = OnSecondaryDark,
    tertiary = TertiaryAmberDark,
    onTertiary = OnTertiaryDark,
    background = BackgroundDark,
    onBackground = TextPrimaryDark,
    surface = SurfaceDark,
    onSurface = TextPrimaryDark,
    surfaceVariant = SurfaceElevatedDark,
    onSurfaceVariant = TextSecondaryDark,
    outline = OutlineDark,
    error = DangerRedDark,
    onError = Color(0xFF4A0B0B)
)

private val VersyLightColors = lightColorScheme(
    primary = PrimarySkyLight,
    onPrimary = OnPrimaryLight,
    primaryContainer = Color(0xFFE0F2FE),
    onPrimaryContainer = PrimarySkyLightDim,
    secondary = SecondaryLilacLight,
    onSecondary = OnSecondaryLight,
    tertiary = TertiaryAmberLight,
    onTertiary = OnTertiaryLight,
    background = BackgroundLight,
    onBackground = TextPrimaryLight,
    surface = SurfaceLight,
    onSurface = TextPrimaryLight,
    surfaceVariant = SurfaceElevatedLight,
    onSurfaceVariant = TextSecondaryLight,
    outline = OutlineLight,
    error = DangerRedLight,
    onError = Color.White
)

@Composable
fun VersyTheme(
    useDarkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit
) {
    val colorScheme = if (useDarkTheme) VersyDarkColors else VersyLightColors
    val extendedColors = if (useDarkTheme) ExtendedColorsDark else ExtendedColorsLight

    val view = LocalView.current
    if (!view.isInEditMode) {
        SideEffect {
            val window = (view.context as Activity).window
            window.statusBarColor = Color.Transparent.toArgb()
            window.navigationBarColor = colorScheme.background.toArgb()
            WindowCompat.getInsetsController(window, view).apply {
                isAppearanceLightStatusBars = !useDarkTheme
                isAppearanceLightNavigationBars = !useDarkTheme
            }
        }
    }

    androidx.compose.runtime.CompositionLocalProvider(
        LocalExtendedColors provides extendedColors
    ) {
        MaterialTheme(
            colorScheme = colorScheme,
            typography = VersyTypography,
            content = content
        )
    }
}

object VersyColors {
    val extended: ExtendedColors
        @Composable
        get() = LocalExtendedColors.current
}
