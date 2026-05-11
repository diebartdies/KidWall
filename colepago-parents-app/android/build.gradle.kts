subprojects {
    tasks.withType<org.gradle.api.tasks.compile.JavaCompile>().configureEach {
        // Some Flutter plugin Android modules still compile with source/target 8.
        // Suppress obsolete-option warnings on newer JDKs.
        options.compilerArgs.add("-Xlint:-options")
    }
}

allprojects {
    repositories {
        google()
        mavenCentral()
    }
}

val newBuildDir: Directory =
    rootProject.layout.buildDirectory
        .dir("../../build")
        .get()
rootProject.layout.buildDirectory.value(newBuildDir)

subprojects {
    val newSubprojectBuildDir: Directory = newBuildDir.dir(project.name)
    project.layout.buildDirectory.value(newSubprojectBuildDir)
}
subprojects {
    project.evaluationDependsOn(":app")
}

tasks.register<Delete>("clean") {
    delete(rootProject.layout.buildDirectory)
}
