// 🧪 ТЕСТОВЫЕ ДАННЫЕ ДЛЯ УЛУЧШЕННОЙ ЛОГИКИ ПОИСКА ГРУЗОВ

// Эмулируем структуру данных availableCargoForPlacement
const testCargoData = [
  // ЗАЯВКА 1: Простая заявка с одним грузом (СЦЕНАРИЙ 1)
  {
    id: "cargo_001",
    cargo_number: "123456",
    cargo_name: "Простой груз 123456",
    placement_status: "awaiting_placement"
  },
  
  // ЗАЯВКА 2: Заявка с несколькими типами грузов (СЦЕНАРИИ 2 и 3)
  {
    id: "cargo_002", 
    cargo_number: "250148",
    cargo_name: "Комплексная заявка 250148",
    placement_status: "awaiting_placement",
    cargo_items: [
      {
        type_number: "01",
        cargo_name: "Электроника",
        quantity: 3,
        individual_items: [
          { unit_index: "01", individual_number: "250148/01/01", placement_status: "awaiting_placement" },
          { unit_index: "02", individual_number: "250148/01/02", placement_status: "awaiting_placement" },
          { unit_index: "03", individual_number: "250148/01/03", placement_status: "awaiting_placement" }
        ]
      },
      {
        type_number: "02", 
        cargo_name: "Одежда",
        quantity: 2,
        individual_items: [
          { unit_index: "01", individual_number: "250148/02/01", placement_status: "awaiting_placement" },
          { unit_index: "02", individual_number: "250148/02/02", placement_status: "awaiting_placement" }
        ]
      }
    ]
  },
  
  // ЗАЯВКА 3: Еще одна простая заявка (СЦЕНАРИЙ 1)
  {
    id: "cargo_003",
    cargo_number: "789012", 
    cargo_name: "Простой груз 789012",
    placement_status: "awaiting_placement"
  }
];

// ТЕСТОВЫЕ СЦЕНАРИИ ДЛЯ ПРОВЕРКИ

console.log("=== ТЕСТ УЛУЧШЕННОЙ ЛОГИКИ ПОИСКА ГРУЗОВ ===\n");

// СЦЕНАРИЙ 1: Простой груз
console.log("🧪 СЦЕНАРИЙ 1: Тестирование простого груза");
const simpleTests = [
  "123456",    // Должен найти cargo_001
  "789012",    // Должен найти cargo_003  
  "999999"     // Не должен найти ничего
];

simpleTests.forEach(qr => {
  console.log(`   QR: "${qr}"`);
  const found = testCargoData.find(item => item.cargo_number === qr);
  console.log(`   Результат: ${found ? found.cargo_name : 'НЕ НАЙДЕН'}\n`);
});

// СЦЕНАРИЙ 2: Груз внутри заявки  
console.log("🧪 СЦЕНАРИЙ 2: Тестирование груза внутри заявки");
const cargoInRequestTests = [
  { qr: "250148.01", request: "250148", type: "01" },  // Должен найти Электронику
  { qr: "250148/02", request: "250148", type: "02" },  // Должен найти Одежду
  { qr: "250148.99", request: "250148", type: "99" }   // Не должен найти тип 99
];

cargoInRequestTests.forEach(test => {
  console.log(`   QR: "${test.qr}" (заявка: ${test.request}, тип: ${test.type})`);
  
  // 1. Найти заявку
  const request = testCargoData.find(item => item.cargo_number === test.request);
  if (request && request.cargo_items) {
    // 2. Найти тип груза
    const cargoItem = request.cargo_items.find(item => item.type_number === test.type);
    console.log(`   Результат: ${cargoItem ? cargoItem.cargo_name : 'ГРУЗ НЕ НАЙДЕН'}\n`);
  } else {
    console.log(`   Результат: ЗАЯВКА НЕ НАЙДЕНА\n`);
  }
});

// СЦЕНАРИЙ 3: Единица груза внутри типа
console.log("🧪 СЦЕНАРИЙ 3: Тестирование единицы груза внутри типа");
const unitTests = [
  { qr: "250148.01.01", request: "250148", type: "01", unit: "01" }, // Должен найти первую единицу электроники
  { qr: "250148/02/02", request: "250148", type: "02", unit: "02" }, // Должен найти вторую единицу одежды
  { qr: "250148.01.99", request: "250148", type: "01", unit: "99" }  // Не должен найти единицу 99
];

unitTests.forEach(test => {
  console.log(`   QR: "${test.qr}" (заявка: ${test.request}, тип: ${test.type}, единица: ${test.unit})`);
  
  // 1. Найти заявку
  const request = testCargoData.find(item => item.cargo_number === test.request);
  if (request && request.cargo_items) {
    // 2. Найти тип груза
    const cargoItem = request.cargo_items.find(item => item.type_number === test.type);
    if (cargoItem && cargoItem.individual_items) {
      // 3. Найти единицу
      const unit = cargoItem.individual_items.find(u => u.unit_index === test.unit);
      console.log(`   Результат: ${unit ? unit.individual_number : 'ЕДИНИЦА НЕ НАЙДЕНА'}\n`);
    } else {
      console.log(`   Результат: ГРУЗ НЕ НАЙДЕН\n`);
    }
  } else {
    console.log(`   Результат: ЗАЯВКА НЕ НАЙДЕНА\n`);
  }
});

console.log("=== ТЕСТ ЗАВЕРШЕН ===");

// Экспорт для использования в браузере
if (typeof window !== 'undefined') {
  window.testCargoData = testCargoData;
  window.runSearchLogicTests = () => {
    console.log("Запуск тестов логики поиска в браузере...");
    // Здесь можно добавить интеграцию с реальными функциями приложения
  };
}