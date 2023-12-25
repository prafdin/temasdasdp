"""
Эта программа реализует сильно упрощённую версию протокола BitTorrent. См.
  - https://www.bittorrent.org/beps/bep_0003.html
  - https://www.bittorrent.org/beps/bep_0015.html
  - https://wiki.theory.org/BitTorrentSpecification

Она позволяет скачивать одну раздачу из torrent-файла в многопоточном режиме,
подключаясь одновременно к нескольким пирам. При закачке проверяются
существующие файлы, и прошедшие проверку куски повторно не загружаются.

При этом не реализованы раздача файлов, а также многие тонкости протокола.
В рамках одного соединения блоки запрашиваются последовательно, поэтому
скорость загрузки невысока. Мягко говоря, есть ещё над чем поработать.

Тестовый torrent-файл взят отсюда:
https://academictorrents.com/details/42714f859770f1a9d8b27985f9f16ea17e8ba2f6
"""

import sys

from client import TorrentClient

filename = 'sample.torrent'
TorrentClient(filename).start()
