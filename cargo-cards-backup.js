// РЕЗЕРВНАЯ КОПИЯ СТАРЫХ КАРТОЧЕК ГРУЗОВ ДЛЯ РАЗМЕЩЕНИЯ
// Сохранено: ${new Date().toLocaleDateString('ru-RU')} 
// Диапазон строк в App.js: 20380-20500

// Старый код карточек:
const OldCargoPlacementCards = () => {
  return (
    <div className="grid gap-4 grid-cols-1 lg:grid-cols-2 xl:grid-cols-3">
      {availableCargoForPlacement.filter(item => item && item.id).map((item) => {
        const warehouseColors = getWarehouseColor(item.warehouse_name);
        return (
          <Card key={`cargo-${item.id}`} className={`${warehouseColors.border} ${warehouseColors.bg} border-l-4`}>
            <CardContent className="p-4">
              <h3 className="font-bold text-lg text-blue-600 mb-2">№{item.cargo_number}</h3>
              <div className="space-y-2 text-sm">
                <div>
                  <span className="font-medium">🏙️ Город выдачи:</span> {item.delivery_city || 'Не указан'}
                </div>
                <div>
                  <span className="font-medium">🏢 Маршрут:</span> {item.source_warehouse_name || 'Неизвестен'} → {item.target_warehouse_name || 'Неизвестен'}
                </div>
                <div>
                  <span className="font-medium">👤 Получатель:</span> {item.recipient_full_name || 'Не указан'}
                </div>
                <div>
                  <span className="font-medium">📅 Принят:</span> {item.created_date ? new Date(item.created_date).toLocaleDateString('ru-RU') : 'Не указано'}
                </div>
                <div>
                  <span className="font-medium">🚚 Способ:</span> {item.delivery_method || 'Не указан'}
                </div>
                <div>
                  <span className="font-medium">💰 Оплата:</span> {item.payment_method || 'Не указан'}
                </div>
              </div>
              
              <div className="bg-gray-50 p-3 rounded-lg mt-3">
                <h4 className="font-medium text-sm mb-2">📦 Список грузов ({(item.cargo_items || []).length} типов)</h4>
                {(item.cargo_items || []).length > 0 ? (
                  item.cargo_items.map((cargoItem, index) => (
                    <div key={index} className="bg-white p-2 rounded border text-xs mb-1">
                      <div className="flex justify-between items-center">
                        <div>
                          <p className="font-medium text-gray-800">
                            Груз{item.cargo_number}/{String(index + 1).padStart(2, '0')} "{cargoItem.cargo_name || `Груз №${index + 1}`}"
                          </p>
                          <p className="text-gray-500 text-xs">
                            {cargoItem.quantity || 1} шт • {cargoItem.weight || 0} кг
                          </p>
                          {/* НОВОЕ: Показываем индивидуальные номера */}
                          {cargoItem.individual_items && cargoItem.individual_items.length > 0 && (
                            <div className="mt-1 flex flex-wrap gap-1">
                              {cargoItem.individual_items.slice(0, 3).map((unit, unitIndex) => (
                                <span 
                                  key={unitIndex} 
                                  className={`px-1 py-0.5 text-xs rounded ${
                                    unit.is_placed 
                                      ? 'bg-green-100 text-green-700' 
                                      : 'bg-gray-100 text-gray-600'
                                  }`}
                                  title={unit.individual_number}
                                >
                                  {unit.individual_number.split('/').slice(-1)[0]}
                                </span>
                              ))}
                              {cargoItem.individual_items.length > 3 && (
                                <span className="px-1 py-0.5 text-xs bg-gray-100 text-gray-500 rounded">
                                  +{cargoItem.individual_items.length - 3}
                                </span>
                              )}
                            </div>
                          )}
                        </div>
                        <div className="text-right">
                          <p className="font-medium text-blue-600">
                            Размещено {cargoItem.placed_count || 0}/{cargoItem.quantity || 1}
                          </p>
                          <p className={`text-xs ${
                            (cargoItem.placed_count || 0) === (cargoItem.quantity || 1) 
                              ? 'text-green-600' 
                              : (cargoItem.placed_count || 0) > 0 
                                ? 'text-yellow-600' 
                                : 'text-red-600'
                          }`}>
                            {(cargoItem.placed_count || 0) === (cargoItem.quantity || 1) 
                              ? 'Размещено' 
                              : (cargoItem.placed_count || 0) > 0 
                                ? 'Частично' 
                                : 'Ждёт'}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="bg-white p-2 rounded border text-xs">
                    <div className="flex justify-between">
                      <div>
                        <p className="font-medium">Груз{item.cargo_number}/01 №1</p>
                        <p className="text-gray-500">1 шт • {item.weight || 0} кг</p>
                      </div>
                      <span className="text-red-600 text-xs">Ждёт размещение</span>
                    </div>
                  </div>
                )}
                
                <div className="mt-2 pt-2 border-t text-sm">
                  <div className="flex justify-between">
                    <span className="font-medium">Общий прогресс:</span>
                    <span className="font-bold text-blue-600">{item.placement_progress || '0/1'}</span>
                  </div>
                </div>
              </div>
              
              <div className="flex flex-wrap gap-2 mt-4">
                <Button onClick={() => openEnhancedPlacementModal(item)} size="sm" className="bg-green-600 hover:bg-green-700">
                  <Grid3X3 className="mr-1 h-3 w-3" />Разместить
                </Button>
                <Button onClick={() => handleOpenCargoPlacementDetails(item)} size="sm" className="bg-purple-600 hover:bg-purple-700">
                  <Settings className="mr-1 h-3 w-3" />Действия
                </Button>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
};