# public_NDSiPU_hack_kibernebo
Решение команды Pulsar для хакатона КиберНебо (Компания АвтоТех + Кафедра НДСиПУ ВМК МГУ)

Запустить из корня по очереди файлы:

```bash
python 0_fm_demodulation.py     # Создаст composite_video.raw
python 1_dc_filter.py           # Создаст 1_filtered_video.raw
python 2_notch_filter.py        # Создаст 2_filtered_video.raw
python 3_low_pass_filter.py     # Создаст 3_filtered_video.raw
python 4_dc_filter.py           # Создаст 4_filtered_video.raw
python 5_normalize.py           # Создаст 5_normalized_video.raw
python 6_hsync.py               # Создаст hsync.raw
python 7_build_frame.py         # Разобьет 5_normalized_video.raw по меткам hsync.raw на кадры и склеит
```


Можно запустить 
```bash
python all_in_one.py
```
Этот скрипт делает всё то же самое (что и срикпты 0..7 выше) + измеряет время разметки hsync


---
Интерактивное окно для подбора параметров фильтров
```bash
python fpv_proc.py
```

---

`plotter.py`  - вспомогательный модуль для отрисовки графиков