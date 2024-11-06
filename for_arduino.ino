#define VIBRO_INTEGRATED_PIN  A4
 
void setup() 
{
  Serial.begin(9600);
}
 
void loop()
{
  // считываем показания уровня вибрации
  int integratedVibroValue = analogRead(VIBRO_INTEGRATED_PIN);
  int vibro = analogRead(A5);
  Serial.println(vibro);
//  Serial.print("\t\t");
//  Serial.println(integratedVibroValue);
  delay(10);
}
