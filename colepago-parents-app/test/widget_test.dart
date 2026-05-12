import 'package:flutter_test/flutter_test.dart';

import 'package:colepago_parents_app/main.dart';

void main() {
  testWidgets('App launches smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const ColePagoKidsApp());
    await tester.pumpAndSettle();

    // The app should render without crashing.
    expect(find.byType(ColePagoKidsApp), findsOneWidget);
  });
}
