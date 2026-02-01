
# save_load/save_load.py

# Pyxel を使ったセーブ・ロードのサンプルコード.
# pickle、jsonなどを使ってセーブ・ロードするサンプル.
# jsonはとりあえず確認できように難読化などは行なっていない.
# 実際にjsonでセーブする場合は、難読化や暗号化などが必要になる場合がある.


import pyxel
import json
import os

import pickle

# `js` モジュールは Pyodide（ブラウザ）環境で提供される.
# ローカル実行（pyxel 実行環境）では存在しないため安全にフォールバックする.
try:
	from js import window
except Exception:
	window = None

from enum import Enum, auto

#print(pyxel.__file__)

# それっぽいデータ構造を定義してみる.

# 言語.
class Language(Enum):
	NONE = auto()
	JP = auto()
	EN = auto()
	MAX = auto()

# 難易度.
class Difficulty(Enum):
	NONE = auto()
	EASY = auto()
	NORMAL = auto()
	HARD = auto()
	MAX = auto()
	DEFAULT = NORMAL

class CharacterID(Enum):
	NONE = auto()
	CHARA_001 = auto()
	CHARA_002 = auto()
	CHARA_003 = auto()

	ENEMY_001 = auto()
	ENEMY_002 = auto()
	ENEMY_003 = auto()
	BOSS_001 = auto()
	MAX = auto()

	CHARA_BEGIN = CHARA_001
	CHARA_END = CHARA_003
	ENEMY_BEGIN = ENEMY_001
	ENEMY_END = BOSS_001

# キャラクターデータ.
class CharacterData:
	def __init__(self):
		self._name = ""
		self._level = 1
		self._exp= 0
		self._hp = 0
		self._mp = 0
		pass
	pass

	@property
	def name(self):
		return self._name
	@name.setter
	def name(self, value):
		self._name = value
		pass
	@property
	def level(self):
		return self._level
	@level.setter
	def level(self, value):
		self._level = value
		pass
	@property
	def exp(self):
		return self._exp
	@exp.setter
	def exp(self, value):
		self._exp = value
		pass
	@property
	def hp(self):
		return self._hp
	@hp.setter
	def hp(self, value):
		self._hp = value
		pass
	@property
	def mp(self):
		return self._mp
	@mp.setter
	def mp(self, value):
		self._mp = value
		pass

	def __repr__(self):
		return f"CharacterData(name={self._name}, level={self._level}, exp={self._exp}, hp={self._hp}, mp={self._mp})"

	def to_dict(self):
		return {
			"name": self._name,
			"level": self._level,
			"exp": self._exp,
			"hp": self._hp,
			"mp": self._mp,
		}

	@staticmethod
	def from_dict(d):
		c = CharacterData()
		c._name = d.get("name", "")
		c._level = d.get("level", 1)
		c._exp = d.get("exp", 0)
		c._hp = d.get("hp", 0)
		c._mp = d.get("mp", 0)
		return c

class OptionData:
	MIN_VOLUME = 0
	MAX_VOLUME = 10

	def __init__(self):
		self._volume_se = 5
		self._volume_voice = 5
		self._volume_bgm = 5

		self._language = Language.JP
		self._difficulty = Difficulty.DEFAULT
		pass
	pass

	@property
	def volume_se(self):
		return self._volume_se
	@property
	def volume_voice(self):
		return self._volume_voice
	@property
	def volume_bgm(self):
		return self._volume_bgm
	@property
	def language(self):
		return self._language
	@property
	def difficulty(self):
		return self._difficulty

	def __repr__(self):
		return f"OptionData(volume_se={self._volume_se}, volume_voice={self._volume_voice}, volume_bgm={self._volume_bgm}, language={self._language}, difficulty={self._difficulty})"

	def to_dict(self):
		return {
			"volume_se": self._volume_se,
			"volume_voice": self._volume_voice,
			"volume_bgm": self._volume_bgm,
			"language": (self._language.name if isinstance(self._language, Enum) else str(self._language)),
			"difficulty": (self._difficulty.name if isinstance(self._difficulty, Enum) else str(self._difficulty)),
		}

	@staticmethod
	def from_dict(d):
		o = OptionData()
		o._volume_se = d.get("volume_se", 5)
		o._volume_voice = d.get("volume_voice", 5)
		o._volume_bgm = d.get("volume_bgm", 5)
		lang_name = d.get("language", "JP")
		try:
			o._language = Language[lang_name]
		except Exception:
			o._language = Language.JP
		diff_name = d.get("difficulty", "NORMAL")
		try:
			o._difficulty = Difficulty[diff_name]
		except Exception:
			o._difficulty = Difficulty.DEFAULT
		return o

class GameData:
	def __init__(self):
		# CHARA_BEGIN から CHARA_END までのキャラクターデータ.
		self._characters = {char_id: CharacterData() for char_id in CharacterID if char_id in (CharacterID.CHARA_BEGIN, CharacterID.CHARA_END)}
		pass
	pass

	@property
	def characters(self):
		return self._characters
	
	def __repr__(self):
		return f"GameData(characters={self._characters})"

	def to_dict(self):
		# convert enum keys to names
		return {str(k.name): v.to_dict() for k, v in self._characters.items()}

	@staticmethod
	def from_dict(d):
		g = GameData()
		# clear default characters and rebuild
		g._characters = {}
		for k, v in (d or {}).items():
			try:
				key = CharacterID[k]
			except Exception:
				continue
			g._characters[key] = CharacterData.from_dict(v)
		return g


class RecordEnemyData:
	def __init__(self):
		self._kill_count = 0
		pass
	pass
	@property
	def kill_count(self):
		return self._kill_count
	@kill_count.setter
	def kill_count(self, value):
		self._kill_count = value
		pass
	def __repr__(self):
		return f"RecordEnemyData(kill_count={self._kill_count})"

	def to_dict(self):
		return {"kill_count": self._kill_count}

	@staticmethod
	def from_dict(d):
		r = RecordEnemyData()
		r._kill_count = d.get("kill_count", 0)
		return r

class RecordData:
	LOG_MAX = 100

	def __init__(self):
		self._play_time = 0

		# ENEMY_BEGIN から ENEMY_END までの討伐記録データ.
		self._enemy_record = {char_id: RecordEnemyData() for char_id in CharacterID if char_id in (CharacterID.ENEMY_BEGIN, CharacterID.ENEMY_END)}

		# ログデータ.
		# テキスト（文字列）の可変長配列（上限は100件）.
		self._log_data = []
		pass

	@property
	def play_time(self):
		return self._play_time
	@play_time.setter
	def play_time(self, value):
		self._play_time = value
		pass
	@property
	def enemy_record(self):
		return self._enemy_record

	# ログ操作メソッド
	def add_log(self, text):
		# ログを追加する.
		# 文字列でない値は文字列化して追加する.
		#最新が末尾に来る形式で、合計が上限を超えたら古いものから削除する.
		if text is None:
			text = ""
		# 確実に文字列にする
		entry = str(text)
		self._log_data.append(entry)
		# 上限を超えたら先頭から削る
		if len(self._log_data) > self.LOG_MAX:
			del self._log_data[0: len(self._log_data) - self.LOG_MAX]

	def get_logs(self):
		# ログ一覧（コピー）を返す.
		# 変更は元に影響を与えない.
		return list(self._log_data)

	def clear_logs(self):
		# すべてのログを削除する.
		self._log_data.clear()

	def __repr__(self):
		return f"RecordData(play_time={self._play_time}, enemy_record={self._enemy_record}, log_data={self._log_data})"

	def to_dict(self):
		return {
			"play_time": self._play_time,
			"enemy_record": {k.name: v.to_dict() for k, v in self._enemy_record.items()},
			"log_data": list(self._log_data),
		}

	@staticmethod
	def from_dict(d):
		r = RecordData()
		r._play_time = d.get("play_time", 0)
		# rebuild enemy_record
		r._enemy_record = {}
		for k, v in (d.get("enemy_record") or {}).items():
			try:
				key = CharacterID[k]
			except Exception:
				continue
			r._enemy_record[key] = RecordEnemyData.from_dict(v)
		# logs
		r._log_data = list(d.get("log_data") or [])
		return r

# セーブデータ.
# システムデータとゲームデータを分けたりするが、ここではまとめて扱う.
class SaveData:
	def __init__(self):
		self._version = 1
		self._option_data = OptionData()
		self._game_data = GameData()
		self._record_data = RecordData()
		pass

	@property
	def version(self):
		return self._version
	@property
	def option_data(self):
		return self._option_data
	@property
	def game_data(self):
		return self._game_data
	@property
	def record_data(self):
		return self._record_data

	def __repr__(self):
		return f"SaveData(version={self._version}, option_data={self._option_data}, game_data={self._game_data}, record_data={self._record_data})"

	def to_dict(self):
		return {
			"version": self._version,
			"option_data": self._option_data.to_dict(),
			"game_data": self._game_data.to_dict(),
			"record_data": self._record_data.to_dict(),
		}

	@staticmethod
	def from_dict(d):
		s = SaveData()
		s._version = int(d.get("version", 1))
		s._option_data = OptionData.from_dict(d.get("option_data", {}))
		s._game_data = GameData.from_dict(d.get("game_data", {}))
		s._record_data = RecordData.from_dict(d.get("record_data", {}))
		return s

	def save_to_file(self, path):
		# ensure directory exists
		dirname = os.path.dirname(path)
		if dirname:
			os.makedirs(dirname, exist_ok=True)
		with open(path, "w", encoding="utf-8") as f:
			json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

	@staticmethod
	def load_from_file(path):
		if not os.path.exists(path):
			return None
		with open(path, "r", encoding="utf-8") as f:
			d = json.load(f)
			return SaveData.from_dict(d)


class App:
	def __init__(self):
		#print(f"App::__init__()")

		print(pyxel.VERSION)

		pyxel.init(320, 240, title="save_load", capture_scale=1)

		pyxel.images[1].load(0, 0, "assets/cat_16x16.png")

		self._x = 160 - 8
		self._y = 120 - 8

		self._vendor: str = None
		self._app_name: str = None
		self._save_data_dir: str = None
		self._save_data_path: str = None

		self._vendor = "takezoh"
		self._app_name = "pyxel_save_load_sample"

		# セーブデータディレクトリの取得.
		if self._vendor is not None and self._app_name is not None:
			self._save_data_dir = pyxel.user_data_dir(self._vendor, self._app_name)
		else:
			# 開発中はカレントディレクトリ以下に保存する.
			self._save_data_dir = "./save/"
		
		print(f"Save data directory: {self._save_data_dir}")

		# セーブデータの作成.
		self._save_data = SaveData()

		# jsonセーブファイルのパス
		self._save_data_json_path = os.path.join(self._save_data_dir, "save_data.json")
		
		# pickleセーブファイルのパス
		self._save_data_pickle_path = os.path.join(self._save_data_dir, "save_data.pkl")

		pyxel.run(self.update, self.draw)

	def update(self):
		if pyxel.btn(pyxel.KEY_RIGHT) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_RIGHT):
			self._x += 1
		if pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_LEFT):
			self._x -= 1
		if pyxel.btn(pyxel.KEY_DOWN) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_DOWN):
			self._y += 1
		if pyxel.btn(pyxel.KEY_UP) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_UP):
			self._y -= 1
		
		if pyxel.btnp(pyxel.KEY_Z):
			# ダミーの値を設定してみる.
			self._save_data.option_data._volume_bgm = 7
			self._save_data.game_data._characters[CharacterID.CHARA_001]._name = "Hero"
			self._save_data.game_data._characters[CharacterID.CHARA_001]._level = 5
			self._save_data.record_data._play_time = 12345
			self._save_data.record_data._enemy_record[CharacterID.ENEMY_001]._kill_count = 10
			self._save_data.record_data.add_log("This is a test log entry.")
			# 
			print(self._save_data)

		if pyxel.btnp(pyxel.KEY_X):
			# ダンプ.
			print(self._save_data)
		
		# jsonセーブ
		if pyxel.btnp(pyxel.KEY_A):
			try:
				self._save_data.save_to_file(self._save_data_json_path)
				#self._save_data.record_data.add_log(f"Saved to {self._save_data_json_path}")
				print(f"Saved: {self._save_data_json_path}")
			except Exception as e:
				print(f"Save error: {e}")

		# jsonロード
		if pyxel.btnp(pyxel.KEY_S):
			try:
				loaded = SaveData.load_from_file(self._save_data_json_path)
				if loaded is not None:
					self._save_data = loaded
					#self._save_data.record_data.add_log(f"Loaded from {self._save_data_json_path}")
					print(f"Loaded: {self._save_data_json_path}")
					print(self._save_data)
				else:
					print("No save file to load")
			except Exception as e:
				print(f"Load error: {e}")
		
		# pickleセーブ
		if pyxel.btnp(pyxel.KEY_Q):
			try:
				# ensure directory exists
				dirname = os.path.dirname(self._save_data_pickle_path)
				if dirname:
					os.makedirs(dirname, exist_ok=True)
				with open(self._save_data_pickle_path, 'wb') as f:
					pickle.dump(self._save_data, f)
				print(f"Pickle saved: {self._save_data_pickle_path}")
			except Exception as e:
				print(f"Pickle save error: {e}")
		
		# pickleロード
		if pyxel.btnp(pyxel.KEY_W):
			try:
				with open(self._save_data_pickle_path, 'rb') as f:
					loaded = pickle.load(f)
				if loaded is not None:
					self._save_data = loaded
					print(f"Pickle loaded: {self._save_data_pickle_path}")
					print(self._save_data)
				else:
					print("No pickle save file to load")
			except Exception as e:
				print(f"Pickle load error: {e}")

		# ローカルストレージセーブ（ブラウザ環境のみ）
		if pyxel.btnp(pyxel.KEY_E):
			if window is not None:
				try:
					data_str = json.dumps(self._save_data.to_dict())
					window.localStorage.setItem("pyxel_save_data", data_str)
					print("Saved to localStorage")
				except Exception as e:
					print(f"localStorage save error: {e}")
			else:
				print("localStorage not available in this environment")
		# ローカルストレージロード（ブラウザ環境のみ）
		if pyxel.btnp(pyxel.KEY_R):
			if window is not None:
				try:
					data_str = window.localStorage.getItem("pyxel_save_data")
					if data_str is not None:
						d = json.loads(data_str)
						loaded = SaveData.from_dict(d)
						self._save_data = loaded
						print("Loaded from localStorage")
						print(self._save_data)
					else:
						print("No localStorage save data found")
				except Exception as e:
					print(f"localStorage load error: {e}")
			else:
				print("localStorage not available in this environment")
		pass

	def draw(self):
		pyxel.cls(1)
		pyxel.text(16, 8, f"frame:{pyxel.frame_count}", 9)

		pyxel.blt(self._x, self._y, 1, 0, 0, 16, 16, 13)
		pass

if __name__ == "__main__":
	App()
