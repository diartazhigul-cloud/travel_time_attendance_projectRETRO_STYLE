# Travel Time vs University Attendance

Python Streamlit website for a mathematical statistics project.

Research question: is there a statistical relationship between travel time to university (minutes) and class attendance (%)?

## How to open in PyCharm

1. Unzip `travel_time_attendance_project.zip`.
2. In PyCharm: **File → Open** and select the unzipped folder `travel_time_attendance_project`.
3. Create a virtual environment if PyCharm asks.
4. Open the Terminal in PyCharm and install packages:

```bash
pip install -r requirements.txt
```

5. Run the website:

```bash
streamlit run app.py
```

6. Open the address shown by Streamlit, usually:

http://localhost:8501

## Как открыть в PyCharm

1. Распакуйте `travel_time_attendance_project.zip`.
2. В PyCharm: **File → Open** и выберите папку `travel_time_attendance_project`.
3. Если PyCharm предложит, создайте виртуальное окружение.
4. В терминале PyCharm:

```bash
pip install -r requirements.txt
```

5. Запуск:

```bash
streamlit run app.py
```

6. Откройте адрес, который покажет Streamlit, обычно http://localhost:8501

## What is inside

- `app.py` — the website (navigation, pages)
- `style.py` — retro-game CSS and Plotly theme
- `.streamlit/config.toml` — dark theme settings
- `data.py` — 34 survey responses
- `cleaning.py` — parsing hours, ranges, percents
- `i18n.py` — English / Russian text
- `requirements.txt` — Python packages

The dashboard includes: about, research question, hypotheses, survey table, data cleaning, descriptive statistics, histograms, scatter plot, box plots, Pearson correlation, linear regression, hypothesis test, year and transport breakdowns, travel-time categories, interpretation, limitations, and conclusion.

Language can be switched in the sidebar (EN / RU).

## Site structure (retro-game layout)

The 17 pages are grouped into 5 "worlds" that follow the research workflow:

1. **Briefing** — Home, About, Research Question, Hypotheses
2. **Data** — Survey Data, Data Cleaning
3. **Analysis** — Descriptive, Visualization, Correlation, Regression, Hypothesis Testing
4. **Bonus levels** — by Year, by Transport, Travel Time Categories
5. **Finale** — Interpretation, Limitations, Conclusion

Every page has a progress bar and BACK / NEXT buttons, so the site can be read like a game from start to finish.

## Структура сайта

17 страниц собраны в 5 «миров» по ходу исследования: Брифинг → Данные → Анализ → Бонус-уровни → Финал. На каждой странице есть полоска прогресса и кнопки НАЗАД / ДАЛЕЕ.
