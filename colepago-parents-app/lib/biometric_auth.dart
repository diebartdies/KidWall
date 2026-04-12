import 'package:local_auth/local_auth.dart';
import 'package:flutter/material.dart';

class BiometricAuth {
  final LocalAuthentication auth = LocalAuthentication();

  Future<bool> authenticate(BuildContext context) async {
    try {
      bool canCheck = await auth.canCheckBiometrics;
      bool isDeviceSupported = await auth.isDeviceSupported();
      if (!canCheck || !isDeviceSupported) {
        return await _showPinDialog(context);
      }
      bool didAuthenticate = await auth.authenticate(
        localizedReason: 'Please authenticate to continue',
        options: const AuthenticationOptions(
          biometricOnly: true,
          stickyAuth: true,
        ),
      );
      if (!didAuthenticate) {
        return await _showPinDialog(context);
      }
      return didAuthenticate;
    } catch (e) {
      return await _showPinDialog(context);
    }
  }

  Future<bool> _showPinDialog(BuildContext context) async {
    String pin = '';
    return await showDialog<bool>(
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
        ) ??
        false;
  }
}
