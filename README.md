# Thermometer-OCR
A simple python script to extract body temperature from lcd on a thermometer.
This code is based on code in https://github.com/yan9yu/sdr.


フォルダに保存された複数の体温計写真の表示を読み取り、フォルダ名、撮影日時などと一緒に体温をファイルにCSV形式で保存する、簡単なPythonスクリプトです。


体温測定後スマホなどで写真撮影。後で表計算ソフトでまとめたいときに使うように作成。


成形や回転等していないため、真上から撮影し、数字は垂直の必要があります。

![検知結果](https://github.com/monoxit/Thermometer-OCR/blob/master/images/taionkei.jpg)

![出力](https://github.com/monoxit/Thermometer-OCR/blob/master/images/tempcsv.png)

# ToDo
* 自動成形
* エラー処理追加
* 精度向上

# Acknowledgments
* The 7 segment fonts images used in the dataset are DSEG fonts by Keshikan.  https://github.com/keshikan/DSEG
