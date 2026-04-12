import 'package:flutter/material.dart';

class AppLocalizations {
  final Locale locale;
  AppLocalizations(this.locale);

  static AppLocalizations? of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations);
  }

  static const _localizedValues = <String, Map<String, String>>{
    'en': {
      'login': 'Login',
      'email': 'Email',
      'password': 'Password',
      'enter_email': 'Enter email',
      'enter_password': 'Enter password',
      'invalid_credentials': 'Invalid credentials',
    },
    'es': {
      'login': 'Iniciar sesión',
      'email': 'Correo',
      'password': 'Contraseña',
      'enter_email': 'Ingrese correo',
      'enter_password': 'Ingrese contraseña',
      'invalid_credentials': 'Credenciales inválidas',
    },
  };

  String get login => _localizedValues[locale.languageCode]!['login']!;
  String get email => _localizedValues[locale.languageCode]!['email']!;
  String get password => _localizedValues[locale.languageCode]!['password']!;
  String get enterEmail =>
      _localizedValues[locale.languageCode]!['enter_email']!;
  String get enterPassword =>
      _localizedValues[locale.languageCode]!['enter_password']!;
  String get invalidCredentials =>
      _localizedValues[locale.languageCode]!['invalid_credentials']!;
}

class AppLocalizationsDelegate extends LocalizationsDelegate<AppLocalizations> {
  const AppLocalizationsDelegate();

  @override
  bool isSupported(Locale locale) => ['en', 'es'].contains(locale.languageCode);

  @override
  Future<AppLocalizations> load(Locale locale) async {
    return AppLocalizations(locale);
  }

  @override
  bool shouldReload(AppLocalizationsDelegate old) => false;
}
