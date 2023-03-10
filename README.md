# med-corpus-analyser
код для веб приложения с отображением данных, извлеченных из корпуса отзывов на лекарства.

ТЗ, которое кидалось дарье (см Сервис №2): https://docs.google.com/document/d/1d1JXs_pmUjncGaYfi8InJPI2fR7zSfE65rYw_K_IehY/edit#heading=h.vrwl6tb2ejn7.

## Описание функционала
Функционал подразумевается примерно такой. Веб-страница на которой можно формировать таблицу, столбцы которой - это атрибуты (Drugname, Drugform, Diseasename, Indication и так далее), а строки - комбинации этих атрибутов встречающихся в одном тексте. То есть, если в одном тексте упоминается Drugname=Ацикловир, Drugname=ацик, Drugform=таблетки, Drugform=мазь, Diseasename=простуда. То в таблице будет строка

| Drugname       | Drugform      | Diseasename | Indication |
|----------------|---------------|-------------|------------|
| Ацикловир/ацик | таблетки/мазь | простуда    | 39.12      |

Пользователь может указать, указать, какие колонки будут в таблице, добавлять фильтры, после чего информация собирается по уже разобранному корпусу и отображается в этой таблице. 

Для работы сервиса, разобранные отзывы скорее всего надо будет перевести в какой-то другой формат, более экономный. Как минимум потому что для работы не нужны полные тексты отзывов. и вообще в текущем формате огромное количество лишней информации для данного случая. Возможно подойдёт какая-то легковесная реляционная субд, и надо привести это все к табличному виду. А может хранить в json, но других каких-то. Этот новый формат надо продумать, и написать скрипт перевода, и добавить его под гит.
Функциональные возможности следующие.

#### Выбор корпуса

По какому корпусу будет собираться статистика. Тот, что у вас сейчас есть - test, будет еще RDRS-3800 (3800 документов) и Auto-800К (800000 отзывов). 800000 будут иметь огромное количество сущностей, поэтому надо предусмотреть какую-то оптимизацию в плане отображения, чтоб не вся таблица отображалась сразу или типа того. 

#### Выбор режима работы контекстов.

Выбор того, как будут рассматриваться контексты. 4 режима: 

- document - значит мы не обращаем внимания на поле Context у сущностей вообще. Если они появились в одном документе, значит считаем, что они появляются вместе и могут образовать строку в таблице.
- mainContext - рассматриваем только основной контекст - сущности, у которых в Context есть 1.
- otherContext - рассматриваем все, кроме основного контекста - сущности, у которых в Context нет 1.
- independent - рассматриваем контексты как отдельные тексты. То есть считаем, что сущности появляются вместе, если у них есть хотя бы один общий номер в Context.

Выбор интересующих атрибутов.
Выбор колонок из которых будет состоять таблица. Колонки могут быть следующие:
- Drugname - названия препаратов,
- Drugname_ATC - атх коды препаратов,
- DrugBrand - является ли 
- Drugform - лекарственная форма
- Drugform_STD - стандартизированная лекарственная форма
- Drugclass - класс препарата
- Drugclass_ATC - класс препарата в виде АТХ кода
- MedMaker - изготовитель препарата
- MedFrom - отечественный препарат или зарубежный
- Frequency - частота приема
- Dosage - дозировка
- Duration время использования
- Route - способ приема
- SourceInfodrug - источник информации о препарате
- SourceInfodrug_STD - стандартизированный вариант источника информации
- ADR - нежелательная реакция
- ADR_MEDDRA - нежелательная реакция приведенная к термину Меддра
- Diseasename - название заболевания
- Diseasename_MKB - МКБ-10 код заболевания
- Indication - симптом
- Indication_MEDDRA - симптом приведенный к термину Меддра, 
- reviews - ссылки на тексты отзывов. Сейчас, насколько я знаю у отзывов в поле meta или filename можно найти ID этого отзыва. Этот id можно подставить в ссылку http://otzovik.com/review_1000239.html и получется ссылка на этот отзыв.
- ADR_flag - флаг, есть ли в тексте упоминание нежелательной реакции
- BNE-Pos - текст, описывающий положительный эффект препарата
- ADE-Neg - текст, описывающий негативный эффект препарата
- NegatedADE - текст, описывающий, что препарат не вызвал никаких изменений
- Worse - текст, описывающий негативную динамику болезни после пропитого курса препарата,
- Worse/ADE-Neg - текст, отмеченный как Worse или ADE-Neg
- BNE-Pos_flag - флаг, есть ли в тексте описание положительных эффектов или нет.
- ADE-Neg_flag - флаг, есть ли в тексте сущности ADE-Neg.
- NegatedADE_flag - флаг, есть ли в тексте сущности NegatedADE.
- Worse_flag - флаг, есть ли в тексте сущности Worse.
- Worse/ADE-Neg_flag - флаг, есть ли в тексте сущности Worse или ADE-Neg.
- Tonality - положительная тональность (если есть только BNE-Pos), отрицательная тональность (если нет BNE-Pos, но есть ADR или ADE-Neg, или Words, или NegatedADE), неопределённая (если нет описания эффектов) или смешанная (есть и положительные и отрицательные). 

Помимо этого, могут быть
- "индексообразующие" колонки (не знаю, как правильней назвать). Это колонки, сочетания которых образуют новые строки. Например, если в одном отзыве указаны Drugname==Арбидол и Diseasename=Грипп, а в другом отзыве Drugname==Арбидол и Diseasename=орви. Тогда, если пользователь укажет как индексообразующие колонки Drugname, Diseasename, тогда строк будет 2.
| Drugname | Diseasename |
|----------|-------------|
| Арбидол  | орви        |
| Арбидол  | Грипп       |
Если указываем как индексообразующую только Drugname, а Diseasename тоже указываем, но как обычную колонку, тогда одна.
| Drugname | Diseasename |
|----------|-------------|
| Арбидол  | орви, Грипп  |

Индексообразующими колонками могут быть:
Drugname, Drugname_ATC, DrugBrand, Drugform, Drugform_STD, Drugclass, Drugclass_ATC, MedMaker, MedFrom, Frequency, Dosage, Duration, Route, SourceInfodrug, SourceInfodrug_STD, ADR,ADR_MEDDRA, Diseasename, Diseasename_MKB, Indication, Indication_MEDDRA
- простые колонки или колонки с множествами. В этих колонках перечисляются все уникальные сущности соответствующего типа, которые встречаются в одних текстах с комбинациями указанных в индексообразующих колонках. Как в примере выше была колонка Diseasename.
Такими колонками могут быть: Drugname, Drugname_ATC, DrugBrand,Drugform, Drugform_STD, Drugclass, Drugclass_ATC, MedMaker, MedFrom, Frequency, Dosage, Duration, Route, SourceInfodrug, SourceInfodrug_STD, ADR, ADR_MEDDRA, Diseasename, Diseasename_MKB, Indication, Indication_MEDDRA, reviews.
- Количественные колонки. В этих колонках указывается количество сущностей соответствующего типа, которые появляются в одних текстах с индексом. Такими колонками могут быть: ADR, ADR_flag, BNE-Pos, BNE-Pos_flag, ADE-Neg, NegatedADE, Worse, ADE-Neg_flag, NegatedADE_flag, Worse_flag, Tonality, Worse/ADE-Neg, Worse/ADE-Neg_flag. Разница между ADR и, например, ADR_flag в том, что если у нас указан индекс Drugname,Diseasename и есть 2 текста, где упоминаются Арбидол и ОРВИ, и в одном тексте упоминается 2 АДР, а в другом один. То в количественной колонке ADR будет 3 (сущности появляется в одник текстах с соответствующей комбинацией из индекс-колонок), а в ADR_flag будет стоять 2 (потому что 2 текста с наличием АДР с соответствующей комбинацией из индекс-колонок).

#### Фильтрация и поиск.

Для индексообразующих колонок нужен какой-то такой функционал. Допустим при клике по названию колонки появляется дополнительное окно, в нём поле ввода и список всех значений для этого атрибута из корпуса. При вводе в поле текста, список начинает фильтроваться и остаются только значения, которые содержат введенный текст. И в этом списке можно отмечать нужные значения. После применения фильтра, в таблице будут отображены только строки у которых в этой колонке присутствуют выбранные значения.

#### Выбор уровня нормализации. 

Тезаурусы MedDRA, ATC, MKB10 имеют иерархическую ( и не только) структуру, и у нас в соответствующих полях могут быть приведены термины разных уровней. Можно добавить опцию - поднять все термины на один какой-то уровень структуры тезауруса. Но это думаю на последок оставить, не самая полезная функция.

#### Выгрузка получившейся таблицы в csv.

Можно в принципе сделать. но опционально

## Структура проекта
#### Подготовка данных
Нужен набор скриптов, которые будут готовить данные (разобранные нейросетками) и загружать их в субд.
Предположительно следующий набор:
- PrepareCorpus - скрипт для предобработки корпуса. Удаляет лишнее и переводит какой-то из входных форматов в один (пока не решил, какой). 
- UpploadCorpusToSQLlight3 - скрипт загрузки предварительно сохранённых данных в базу данных sqlight3 (питоновский пакет)
- UpploadCorpusToMariaDB - скрипт загрузки предварительно сохранённых данных в базу данных mariaDB
#### База данных
Не знаю, есть ли разница - хранить данные в sql базу или nosql. Наверно выбор между mariadb и elasticsearch. Потому что mariadb это альтернатива mysql, которая рекомендуется при установке Inception (система разметки), а с elasticsearch есть опыт работы и в нем есть нечеткий полнотекстовый поиск.
Структура базы должна быть наверно такая:

##### Простой вариант структуры базы данных
Под каждый атрибут своя таблица, или одна единая для всего?
Всё в одной - большая и дополнительная колонка с типом. Разные - постоянные join.
Колонки:
- index
- text - текст сущности
- mention_type - в случае, если храним все в одной таблице
- context - номер контекста (одного). Если у упоминия несколько контекстов, то будет несколько строк, где это поле отличается.
- origin - задан только у Drugname и MedMaker в зависимости от атрибута MedFrom и MedMaker
- review_url - придётся восстанавливать из названий файлов - вот это возможно стоит вынести в отдельную таблицу, а здесь id оставить, как и нормализацию
- norm_value - результат нормализации. не атомарный атрибут =/

##### Сложный вариант структуры базы данных
Возможно более правилный варианта, но не уверен, как его эффективно организовать.
Надо ли под каждый атрибут отдельную таблицу? это ведь постоянные джоины. С одной таблицей наверно не получится, это селфджоины или типа того надо делать, хз.
Под каждый атрибут своя таблица с упоминаниями, где строки - выделенные упоминания, а колонки:
- mention_index
- text - текст сущности
- medFrom - только для драгнейма.
- MedMaker - тодлько для MedMaker
дополнительные таблицы:

таблица сопоявления
- mention_index
- context - номер контекста (одного). Если у упоминия несколько контекстов, то будет несколько строк, где это поле отличается.
- review_index - 
- mention_type - тип сущности, одинаковый с названием таблицы сущностей.

Нормализационные пары - таблица под каждый атрибут+название тезауруса. Вопрос, хранить ли пары для всех уровней или только для нижнего.
- pair_n_index
- mention_index - индекс одной сущности
- norm_term_index - индекс одного термина

Нормализационные тезаурусы. под каждый тезаурус отдельная таблица. Вопрос, как иерархию сохранить
- norm_term_index
- term
- parent(s) ? или level? 

reviews
- review_id
- review_url

##### Альтернативный вариант
Храним в эластиксёрч индекс, где каждая строка - это отзыв (или контекст, если используем их). колонки - все, которые возможны для запроса. При выборе активных колонок, и условий поиска производится запрос к эластику, с дропом ненужных колонок и групбаем по нужным для получения количества отзывов итп. Надо разобраться, как это сделать.

#### Сервисные скрипты
Тут пока не ясно.
Варианты:
- flask+react. Это первое, что приходит в голову. С фласком более менее понятно, через него можно организовать интерфейс доступа к эластику. А реакт, потому что можно будет встроить web GUI в проект дарьи с демкой, как дополнительную страницу.
- flask. Можно все сделать на фласке с ним я более знаком. 
- react. Можно все сделать на реакте, наверно, но не знаю, как.
- ???
Если фласк, то нужен скрипт 
- X.py - содержащий функции с запросами (для формирования селект запросов) и постобработки данных.
- service.py - сервис, принимающий запросы от браузера/фронта и вызывающий соответствующие функции

# Более простой вариант
Загружаем в эластик таблицу с предварительно определёнными полями, и делаем только поиск.
Поля таблицы:
Drugnames, Diseasenames, Indications, ADRs, ADR_reviews_count, Negated_ADE_reviews_count, Neg_reviews_count, Pos_reviews_count, review_count, review_urls.
В полях Drugnames, Diseasenames, Indications, ADRs должны лежать нормализационные варианты. Сейчас только для драгнеймов и дизиснеймов была сделана нормализация с помощью pymorphy. Для ADR и Indication должны быть термины меддры, а поиск с вариациями должен быть реализован через словарь синонимов наверно.

## TODO
1. Набросать юз-кейсы, с иллюстрациями. Вынести на обсуждение. Либо просто собрать демо версию и вынести на обсуждение.
2. Написать скрипт перевода в предварительный формат для малой базы данных. Сделать это так, чтоб функции потом можно было использовать для большой. Но я не знаю, стоит ли её сохранять, стоит ли её при этом как-то сжимать или сразу загружать в базу по мере обработки.
3. Запихнуть собранные данные в SQLIGHT3 (питоновский пакет)
4. Написать функции, которые будут делать запросы к базе для запланированных юз-кейсов.
5. Сделать сервис на фласке, который будет использовать эти функции по запросам от пользователя.
6. Добавить страницу в реакт приложение с прошлой демкой для демонстации.
7. Попробовать сделать тоже для большого количества данных c mariaDB (скорее всего)