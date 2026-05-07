plugins {
    id("com.android.application")
    // The Flutter Gradle Plugin must be applied after the Android Gradle plugin.
    id("dev.flutter.flutter-gradle-plugin")
}

android {
    compileSdk = flutter.compileSdkVersion
    ndkVersion = "28.2.13676358"

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_21
        targetCompatibility = JavaVersion.VERSION_21
    }

    kotlinOptions {
        jvmTarget = JavaVersion.VERSION_21.toString()
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
