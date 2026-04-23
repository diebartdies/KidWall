import 'package:camera/camera.dart';
import 'package:google_mlkit_face_detection/google_mlkit_face_detection.dart';
import 'package:flutter/services.dart';
import 'package:flutter/material.dart';

/// Widget that uses the selfie camera to detect faces and notifies if more than one face is present.
class FaceObscureDetector extends StatefulWidget {
  final Widget child;
  final void Function(bool shouldObscure) onFaceDetection;
  const FaceObscureDetector({
    super.key,
    required this.child,
    required this.onFaceDetection,
  });

  @override
  State<FaceObscureDetector> createState() => _FaceObscureDetectorState();
}

class _FaceObscureDetectorState extends State<FaceObscureDetector> {
  CameraController? _controller;
  bool _obscure = false;
  late FaceDetector _faceDetector;
  bool _processing = false;

  @override
  void initState() {
    super.initState();
    _initCamera();
    _faceDetector = FaceDetector(options: FaceDetectorOptions());
  }

  Future<void> _initCamera() async {
    final cameras = await availableCameras();
    final front = cameras.firstWhere(
      (c) => c.lensDirection == CameraLensDirection.front,
    );
    _controller = CameraController(
      front,
      ResolutionPreset.low,
      enableAudio: false,
    );
    await _controller!.initialize();
    _controller!.startImageStream(_processCameraImage);
    setState(() {});
  }

  Future<void> _processCameraImage(CameraImage image) async {
    if (_processing) return;
    _processing = true;
    final WriteBuffer allBytes = WriteBuffer();
    for (final Plane plane in image.planes) {
      allBytes.putUint8List(plane.bytes);
    }
    final bytes = allBytes.done().buffer.asUint8List();
    final InputImageMetadata meta = InputImageMetadata(
      size: Size(image.width.toDouble(), image.height.toDouble()),
      rotation: InputImageRotation.rotation0deg,
      format:
          InputImageFormatValue.fromRawValue(image.format.raw) ??
          InputImageFormat.nv21,
      bytesPerRow: image.planes.first.bytesPerRow,
    );
    final inputImage = InputImage.fromBytes(bytes: bytes, metadata: meta);
    final faces = await _faceDetector.processImage(inputImage);
    final shouldObscure = faces.length > 1;
    if (shouldObscure != _obscure) {
      setState(() {
        _obscure = shouldObscure;
      });
      widget.onFaceDetection(_obscure);
    }
    _processing = false;
  }

  @override
  void dispose() {
    _controller?.dispose();
    _faceDetector.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return widget.child;
  }
}

/// Utility to obscure sensitive text
String obscureIfNeeded(String value, bool obscure) {
  if (!obscure) return value;
  return '*' * value.length;
}
