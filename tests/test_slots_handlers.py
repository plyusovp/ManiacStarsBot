# tests/test_slots_handlers.py

import pytest
from unittest.mock import AsyncMock, MagicMock
from handlers.slots_handlers import get_reels_from_dice


class TestSlotsLogic:
    """Тесты для логики слотов"""
    
    def test_get_reels_from_dice(self):
        """Тест функции разбора значения дайса на три барабана"""
        # Тестируем различные значения дайса
        test_cases = [
            (1, (0, 0, 0)),   # BAR BAR BAR
            (2, (1, 0, 0)),   # Grapes BAR BAR
            (5, (0, 1, 0)),   # BAR Grapes BAR
            (17, (0, 0, 1)),  # BAR BAR Grapes
            (64, (3, 3, 3)),  # Seven Seven Seven
            (4, (3, 0, 0)),   # Seven BAR BAR
        ]
        
        for dice_value, expected_reels in test_cases:
            result = get_reels_from_dice(dice_value)
            assert result == expected_reels, f"Для дайса {dice_value} ожидалось {expected_reels}, получено {result}"
    
    def test_slots_win_conditions(self):
        """Тест условий выигрыша в слотах"""
        # Три семерки (максимальный выигрыш)
        assert get_reels_from_dice(64) == (3, 3, 3)  # Seven Seven Seven
        
        # Три одинаковых (не семерки)
        assert get_reels_from_dice(1) == (0, 0, 0)    # BAR BAR BAR
        assert get_reels_from_dice(2) == (1, 0, 0)    # НЕ три одинаковых
        
        # Два одинаковых (должно запускать повторный бросок)
        # Проверяем, что некоторые комбинации дают два одинаковых
        reels = get_reels_from_dice(2)  # (1, 0, 0) - не два одинаковых подряд
        reels = get_reels_from_dice(3)  # (2, 0, 0) - не два одинаковых подряд
        
        # Найдем комбинации с двумя одинаковыми подряд
        found_two_match = False
        for dice_val in range(1, 65):
            reel1, reel2, reel3 = get_reels_from_dice(dice_val)
            if (reel1 == reel2) or (reel2 == reel3):
                found_two_match = True
                break
        
        assert found_two_match, "Не найдено комбинаций с двумя одинаковыми подряд"
    
    def test_slots_lose_conditions(self):
        """Тест условий проигрыша в слотах"""
        # Все разные символы
        found_all_different = False
        for dice_val in range(1, 65):
            reel1, reel2, reel3 = get_reels_from_dice(dice_val)
            if reel1 != reel2 and reel2 != reel3 and reel1 != reel3:
                found_all_different = True
                break
        
        assert found_all_different, "Не найдено комбинаций со всеми разными символами"


if __name__ == "__main__":
    # Запуск тестов
    test_instance = TestSlotsLogic()
    
    print("Запуск тестов логики слотов...")
    
    try:
        test_instance.test_get_reels_from_dice()
        print("✅ Тест get_reels_from_dice прошел успешно")
        
        test_instance.test_slots_win_conditions()
        print("✅ Тест условий выигрыша прошел успешно")
        
        test_instance.test_slots_lose_conditions()
        print("✅ Тест условий проигрыша прошел успешно")
        
        print("\n🎉 Все тесты прошли успешно!")
        
    except Exception as e:
        print(f"❌ Тест провалился: {e}")
        raise
