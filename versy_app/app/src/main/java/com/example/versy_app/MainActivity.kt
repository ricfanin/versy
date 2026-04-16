package com.example.versy_app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import com.example.versy_app.ui.navigation.AppNavigation
import com.example.versy_app.ui.theme.VersyTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            VersyTheme {
                AppNavigation()
            }
        }
    }
}
