// ignore_for_file: use_build_context_synchronously

import 'package:local_auth/local_auth.dart';
import 'package:flutter/material.dart';
import 'dart:developer';

enum BiometricTypeOption { fingerprint, face, iris }

class BiometricAuth {
  final LocalAuthentication auth = LocalAuthentication();

  /// Allowed methods can be configured by parents and passed in.
  Future<bool> authenticate(
    BuildContext context, {
    List<BiometricTypeOption>? allowedMethods,
  }) async {
    try {
      bool canCheck = await auth.canCheckBiometrics;
      bool isDeviceSupported = await auth.isDeviceSupported();
      if (!canCheck || !isDeviceSupported) {
        log('Biometrics not available or not supported. Falling back to PIN.');
        return await _showPinDialog(context);
      }

      // Get available biometrics
      final availableBiometrics = await auth.getAvailableBiometrics();
      List<BiometricTypeOption> availableOptions = [];
      if (availableBiometrics.contains(BiometricType.fingerprint)) {
        availableOptions.add(BiometricTypeOption.fingerprint);
      }
      if (availableBiometrics.contains(BiometricType.face)) {
        availableOptions.add(BiometricTypeOption.face);
      }
      if (availableBiometrics.contains(BiometricType.iris)) {
        availableOptions.add(BiometricTypeOption.iris);
      }

      // If parent config provided, filter
      if (allowedMethods != null && allowedMethods.isNotEmpty) {
        availableOptions = availableOptions
            .where((o) => allowedMethods.contains(o))
            .toList();
      }

      if (availableOptions.isEmpty) {
        log('No allowed biometrics available. Falling back to PIN.');
        return await _showPinDialog(context);
      }

      // Build list of strings for auth
      List<BiometricType> types = [];
      if (availableOptions.contains(BiometricTypeOption.fingerprint)) {
        types.add(BiometricType.fingerprint);
      }
      if (availableOptions.contains(BiometricTypeOption.face)) {
        types.add(BiometricType.face);
      }
      if (availableOptions.contains(BiometricTypeOption.iris)) {
        types.add(BiometricType.iris);
      }

      bool didAuthenticate = false;
      try {
        didAuthenticate = await auth.authenticate(
          localizedReason: 'Please authenticate to continue',
          biometricOnly: true,
          persistAcrossBackgrounding: true,
          // useErrorDialogs removed in local_auth 3.x
        );
      } catch (e) {
        log(
          'Biometric authentication error: '
          '${e.toString()}. Falling back to PIN.',
        );
      }
      if (!didAuthenticate) {
        return await _showPinDialog(context);
      }
      return didAuthenticate;
    } catch (e) {
      log('Biometric setup error: ${e.toString()}. Falling back to PIN.');
      return await _showPinDialog(context);
    }
  }

  Future<bool> _showPinDialog(BuildContext context) async {
    String pin = '';
    final result = await showDialog<bool>(
      context: context,
      barrierDismissible: false,
      builder: (context) {
        return AlertDialog(
          title: const Text('Enter PIN'),
          content: TextField(
            obscureText: true,
            keyboardType: TextInputType.number,
            onChanged: (value) => pin = value,
            decoration: const InputDecoration(hintText: 'PIN'),
          ),
          actions: [
            TextButton(
              onPressed: () {
                // Replace '1234' with the actual PIN logic
                Navigator.of(context).pop(pin == '1234');
              },
              child: const Text('OK'),
            ),
          ],
        );
      },
    );
    return result ?? false;
  }
}
