plugins {
    id("com.android.application")
    id("kotlin-android")
    // The Flutter Gradle Plugin must be applied after the Android and Kotlin Gradle plugins.
    id("dev.flutter.flutter-gradle-plugin")
}

android {
    compileSdk = flutter.compileSdkVersion
    ndkVersion = flutter.ndkVersion

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = JavaVersion.VERSION_17.toString()
    }

    defaultConfig {
        minSdk = flutter.minSdkVersion
        targetSdk = flutter.targetSdkVersion
        versionCode = flutter.versionCode
        versionName = flutter.versionName
    }


    flavorDimensions += listOf("app")
    productFlavors {
        create("kids") {
            dimension = "app"
            applicationId = "colepago.kids"
            manifestPlaceholders["appLabel"] = "colepago-kids"
            namespace = "colepago.kids"
        }
        create("parents") {
            dimension = "app"
            applicationId = "colepago.parents"
            manifestPlaceholders["appLabel"] = "colepago-parents"
            namespace = "colepago.parents"
        }
    }

    buildTypes {
        release {
            signingConfig = signingConfigs.getByName("debug")
        }
    }
}

flutter {
    source = "../.."
}
