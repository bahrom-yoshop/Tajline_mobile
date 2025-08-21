/**
 * Система нумерации для разработки
 * Все страницы, модали, формы и карточки имеют уникальные номера
 */

export const DEV_NUMBERS = {
  // СТРАНИЦЫ (P001-P999)
  pages: {
    'login': { id: 'P001', label: 'Страница входа' },
    'dashboard': { id: 'P002', label: 'Главная панель' },
    'admin-dashboard': { id: 'P003', label: 'Панель администратора' },
    'courier-dashboard': { id: 'P004', label: 'Панель курьера' },
    'cargo-placement': { id: 'P005', label: 'Размещение грузов' },
    'loading': { id: 'P006', label: 'Страница загрузки' },
  },

  // МОДАЛЬНЫЕ ОКНА (M001-M999)
  modals: {
    'cargo-acceptance': { id: 'M001', label: 'Прием груза' },
    'user-status': { id: 'M002', label: 'Статус пользователя' },
    'login-error': { id: 'M003', label: 'Ошибка входа' },
    'notification-details': { id: 'M004', label: 'Детали уведомления' },
    'contact': { id: 'M005', label: 'Связаться с нами' },
    'user-actions': { id: 'M006', label: 'Действия пользователя' },
    'courier-actions': { id: 'M007', label: 'Действия курьера' },
    'cargo-actions': { id: 'M008', label: 'Действия с грузом' },
    'warehouse-actions': { id: 'M009', label: 'Действия склада' },
    'placement-actions': { id: 'M010', label: 'Действия размещения' },
    'qr-print': { id: 'M011', label: 'Печать QR кодов' },
    'individual-unit-actions': { id: 'M012', label: 'Действия с единицей' },
    'mass-qr-print': { id: 'M013', label: 'Массовая печать QR' },
    'warehouse-selection': { id: 'M014', label: 'Выбор склада' },
    'qr-generation': { id: 'M015', label: 'Генерация QR кодов' },
  },

  // ФОРМЫ (F001-F999)
  forms: {
    'login': { id: 'F001', label: 'Форма входа' },
    'register': { id: 'F002', label: 'Форма регистрации' },
    'cargo-acceptance': { id: 'F003', label: 'Форма приема груза' },
    'user-create': { id: 'F004', label: 'Создание пользователя' },
    'user-edit': { id: 'F005', label: 'Редактирование пользователя' },
    'warehouse-create': { id: 'F006', label: 'Создание склада' },
    'warehouse-edit': { id: 'F007', label: 'Редактирование склада' },
    'courier-create': { id: 'F008', label: 'Создание курьера' },
    'search': { id: 'F009', label: 'Форма поиска' },
    'tracking': { id: 'F010', label: 'Форма отслеживания' },
    'scanner': { id: 'F011', label: 'Форма сканера' },
    'placement': { id: 'F012', label: 'Форма размещения' },
  },

  // КАРТОЧКИ (C001-C999)
  cards: {
    'notification': { id: 'C001', label: 'Карточка уведомления' },
    'cargo-item': { id: 'C002', label: 'Карточка груза' },
    'user-item': { id: 'C003', label: 'Карточка пользователя' },
    'courier-item': { id: 'C004', label: 'Карточка курьера' },
    'warehouse-item': { id: 'C005', label: 'Карточка склада' },
    'placement-item': { id: 'C006', label: 'Карточка размещения' },
    'individual-unit': { id: 'C007', label: 'Карточка единицы груза' },
    'cargo-request': { id: 'C008', label: 'Карточка заявки' },
    'dashboard-stats': { id: 'C009', label: 'Карточка статистики' },
    'warehouse-stats': { id: 'C010', label: 'Статистика склада' },
    'route-info': { id: 'C011', label: 'Информация маршрута' },
    'scanner-step': { id: 'C012', label: 'Этап сканирования' },
    'placement-progress': { id: 'C013', label: 'Прогресс размещения' },
  },

  // КОМПОНЕНТЫ (CP001-CP999)
  components: {
    'sidebar': { id: 'CP001', label: 'Боковое меню' },
    'header': { id: 'CP002', label: 'Заголовок' },
    'notification-dropdown': { id: 'CP003', label: 'Выпадающие уведомления' },
    'user-menu': { id: 'CP004', label: 'Меню пользователя' },
    'pagination': { id: 'CP005', label: 'Пагинация' },
    'filters': { id: 'CP006', label: 'Фильтры' },
    'search-bar': { id: 'CP007', label: 'Строка поиска' },
    'qr-scanner': { id: 'CP008', label: 'QR сканер' },
    'route-map': { id: 'CP009', label: 'Карта маршрута' },
    'yandex-map': { id: 'CP010', label: 'Яндекс карта' },
    'courier-tracking': { id: 'CP011', label: 'Отслеживание курьера' },
  },

  // СЕКЦИИ (S001-S999)
  sections: {
    'dashboard-main': { id: 'S001', label: 'Основная секция панели' },
    'admin-users': { id: 'S002', label: 'Управление пользователями' },
    'admin-couriers': { id: 'S003', label: 'Управление курьерами' },
    'admin-warehouses': { id: 'S004', label: 'Управление складами' },
    'operator-cargo': { id: 'S005', label: 'Работа с грузами' },
    'operator-placement': { id: 'S006', label: 'Размещение грузов' },
    'operator-pickup': { id: 'S007', label: 'Забор груза' },
    'courier-requests': { id: 'S008', label: 'Заявки курьера' },
    'courier-history': { id: 'S009', label: 'История курьера' },
    'notifications': { id: 'S010', label: 'Секция уведомлений' },
    'analytics': { id: 'S011', label: 'Аналитика' },
    'scanner-interface': { id: 'S012', label: 'Интерфейс сканера' },
    'placement-list': { id: 'S013', label: 'Список размещения' },
    'cargo-list': { id: 'S014', label: 'Список грузов' },
  }
};

/**
 * Получить информацию о номере разработчика по типу и ключу
 */
export const getDevNumber = (type, key) => {
  if (!DEV_NUMBERS[type] || !DEV_NUMBERS[type][key]) {
    console.warn(`DevNumber not found: ${type}.${key}`);
    return { id: 'X000', label: `Unknown ${type}` };
  }
  return DEV_NUMBERS[type][key];
};

/**
 * Получить все номера определенного типа
 */
export const getDevNumbersByType = (type) => {
  return DEV_NUMBERS[type] || {};
};