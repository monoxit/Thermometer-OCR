# Thermometer-OCR
A simple python script to extract body temperature from lcd on a thermometer.
This code is based on code in https://github.com/yan9yu/sdr.


フォルダに保存された複数の体温計写真の表示を読み取り、フォルダ名、撮影日時などと一緒に体温をファイルにCSV形式で保存する、簡単なPythonスクリプトです。


体温測定後スマホなどで写真撮影。後で表計算ソフトでまとめたいときに使うように作成。

![検知結果](https://github.com/monoxit/Thermometer-OCR/blob/master/images/taionkei.jpg)

成形や回転等していないため、真上から、数値が垂直になるように撮影する必要があります。

# ToDo
* 自動成形と回転
* エラー処理追加
* 精度向上
