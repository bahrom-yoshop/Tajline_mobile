import React from 'react';
import { Button } from './ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-react';

const DataPagination = ({ 
  pagination, 
  onPageChange, 
  onPerPageChange,
  className = "" 
}) => {
  if (!pagination) {
    return null;
  }

  const { 
    page, 
    per_page, 
    total_pages, 
    total_count, 
    has_next, 
    has_prev,
    next_page,
    prev_page 
  } = pagination;

  const getPageNumbers = () => {
    const delta = 2;
    const range = [];
    const rangeWithDots = [];

    // Если всего страниц мало, показываем все
    if (total_pages <= 7) {
      for (let i = 1; i <= total_pages; i++) {
        range.push(i);
      }
      return range;
    }

    // Добавляем страницы вокруг текущей
    for (
      let i = Math.max(2, page - delta);
      i <= Math.min(total_pages - 1, page + delta);
      i++
    ) {
      range.push(i);
    }

    // Добавляем первую страницу и троеточие если нужно
    if (page - delta > 2) {
      rangeWithDots.push(1, '...');
    } else {
      rangeWithDots.push(1);
    }

    rangeWithDots.push(...range);

    // Добавляем троеточие и последнюю страницу если нужно
    if (page + delta < total_pages - 1) {
      rangeWithDots.push('...', total_pages);
    } else if (total_pages > 1 && !rangeWithDots.includes(total_pages)) {
      rangeWithDots.push(total_pages);
    }

    return rangeWithDots;
  };

  if (total_pages <= 1) {
    return (
      <div className={`flex items-center justify-between p-4 ${className}`}>
        <div className="text-sm text-gray-700">
          Всего: {total_count} {total_count === 1 ? 'элемент' : total_count < 5 ? 'элемента' : 'элементов'}
        </div>
        {onPerPageChange && (
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-700">Показать:</span>
            <Select value={per_page.toString()} onValueChange={onPerPageChange}>
              <SelectTrigger className="w-20">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="10">10</SelectItem>
                <SelectItem value="25">25</SelectItem>
                <SelectItem value="50">50</SelectItem>
                <SelectItem value="100">100</SelectItem>
              </SelectContent>
            </Select>
          </div>
        )}
      </div>
    );
  }

  const startItem = (page - 1) * per_page + 1;
  const endItem = Math.min(page * per_page, total_count);

  return (
    <div className={`flex flex-col sm:flex-row items-center justify-between p-4 border-t space-y-4 sm:space-y-0 ${className}`}>
      {/* Информация о показанных элементах */}
      <div className="text-sm text-gray-700">
        Показано {startItem}-{endItem} из {total_count} {total_count === 1 ? 'элемента' : total_count < 5 ? 'элементов' : 'элементов'}
      </div>
      
      {/* Навигация и настройки */}
      <div className="flex items-center space-x-4">
        {/* Выбор количества элементов на странице */}
        {onPerPageChange && (
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-700">Показать:</span>
            <Select value={per_page.toString()} onValueChange={onPerPageChange}>
              <SelectTrigger className="w-20">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="10">10</SelectItem>
                <SelectItem value="25">25</SelectItem>
                <SelectItem value="50">50</SelectItem>
                <SelectItem value="100">100</SelectItem>
              </SelectContent>
            </Select>
          </div>
        )}

        {/* Кнопки навигации */}
        <div className="flex items-center space-x-1">
          {/* Первая страница */}
          <Button
            variant="outline"
            size="sm"
            onClick={() => onPageChange(1)}
            disabled={!has_prev}
            className="h-8 w-8 p-0"
            title="Первая страница"
          >
            <ChevronsLeft className="h-4 w-4" />
          </Button>

          {/* Предыдущая страница */}
          <Button
            variant="outline"
            size="sm"
            onClick={() => onPageChange(prev_page)}
            disabled={!has_prev}
            className="h-8 w-8 p-0"
            title="Предыдущая страница"
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>

          {/* Номера страниц */}
          <div className="flex items-center space-x-1">
            {getPageNumbers().map((pageNum, index) => (
              <Button
                key={index}
                variant={pageNum === page ? "default" : "outline"}
                size="sm"
                onClick={() => typeof pageNum === 'number' && onPageChange(pageNum)}
                disabled={typeof pageNum !== 'number'}
                className={`h-8 min-w-[2rem] ${
                  typeof pageNum !== 'number' 
                    ? 'cursor-default border-none bg-transparent hover:bg-transparent text-gray-400' 
                    : ''
                } ${pageNum === page ? 'bg-blue-600 text-white hover:bg-blue-700' : ''}`}
              >
                {pageNum}
              </Button>
            ))}
          </div>

          {/* Следующая страница */}
          <Button
            variant="outline"
            size="sm"
            onClick={() => onPageChange(next_page)}
            disabled={!has_next}
            className="h-8 w-8 p-0"
            title="Следующая страница"
          >
            <ChevronRight className="h-4 w-4" />
          </Button>

          {/* Последняя страница */}
          <Button
            variant="outline"
            size="sm"
            onClick={() => onPageChange(total_pages)}
            disabled={!has_next}
            className="h-8 w-8 p-0"
            title="Последняя страница"
          >
            <ChevronsRight className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
};

export default DataPagination;