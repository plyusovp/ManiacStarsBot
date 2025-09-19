import { defineConfig } from 'vite'

export default defineConfig({
  // Базовый URL для GitHub Pages. Тут всё правильно.
  base: '/ManiacStarsBot/',

  // Настройки сборки
  build: {
    // Куда складывать результат.
    // '../docs' означает: "выйти из текущей папки (frontend) на уровень вверх
    // и там создать/использовать папку docs".
    outDir: '../docs'
  }
})
