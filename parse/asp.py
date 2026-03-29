import json
import sys

from utli.logger import timber
from utli import sheet
from utli.cfg_read import cfg

from .npdb import level_table, aka_db


class ASPParser:
    def __init__(self, db_dir: str, map_size: int, card_num: str, reserve: int = 3):

        # load sdvx@asphyxia.db
        raw_data = open(db_dir, 'r')
        self.music_map = [[False, 0, 0, 0, 0, 0, 0, 0] + [False] * reserve for _ in range(map_size * 5 + 1)]
        """music_map is a comprehensive map to store player's play record
        It contains 5-time of map_size lines, each 5 lines define the 5 difficulties of a single song
        Each line of music map should be:
        [
            0: is_recorded(bool), 
            1: mid(int), 
            2: music_type(int), 
            3: score(int), 
            4: clear(int), 
            5: grade(int), 
            6: timestamp(int), 
            7: exscore(int),
            8+: reservation,
        ]
        """

        self.skill, self.last_index, last_time = 0, 0, 0
        skill_time, profile_time, crew_time = 0, 0, 0
        for line in raw_data:
            json_dict = json.loads(line)

            # some lines have no collection name, pass them
            try:
                line_type = json_dict['collection']
            except KeyError:
                continue

            # some lines have no refid or timestamp, pass them anyway
            try:
                cur_id = json_dict['__refid']
                cur_time = json_dict['updatedAt']['$$date']
            except KeyError:
                continue

            # Specify user
            if cur_id != card_num:
                continue

            # music record, contains everything about this play
            if line_type == 'music':

                mid, m_type, score = json_dict['mid'], json_dict['type'], json_dict['score']
                # 1. 原始数据提取
                clear = json_dict['clear']
                score = json_dict['score']
                grade = json_dict['grade']
                version = json_dict.get('version', 6) # 没有标注版本的，默认当做 6 代老数据

                # ==========================================
                # 🚀 开始：6 代 -> 7 代 数据标准化转换器 🚀
                # ==========================================
                
                # 第一步：老数据平滑升级
                if version < 7:
                    if clear == 4:
                        clear = 5      # 6代 UC (4) -> 升级为 7代 UC (5)
                    elif clear == 5:
                        clear = 6      # 6代 PUC (5) -> 升级为 7代 PUC (6)
                    elif clear == 7:
                        clear = 5      # 修复 6代 幽灵错乱数据 (7) -> 强制归为 UC (5)

                # 第二步：分数终极防线（绝对真理，无视任何版本的错误代号）
                if score == 10000000:
                    clear = 6          # 只要是满分，天王老子来了也是 PUC (6)
                elif clear == 6 and score < 10000000:
                    clear = 5          # 如果没满分却拿了 PUC (6)，强制没收，降级为 UC (5)
                m_time = cur_time

                try:
                    exscore = json_dict['exscore']
                except KeyError:
                    exscore = 0

                cur_index = mid * 5 + m_type
                self.music_map[cur_index][0] = True
                self.music_map[cur_index][1] = mid
                self.music_map[cur_index][2] = m_type
                self.music_map[cur_index][3] = score
                self.music_map[cur_index][4] = clear
                self.music_map[cur_index][5] = grade
                self.music_map[cur_index][6] = m_time
                self.music_map[cur_index][7] = exscore

                if m_time > last_time:
                    last_time = m_time
                    self.last_index = cur_index

            # profile record, contains username, appeal card, aka name
            elif line_type == 'profile':
                if cur_time > profile_time:
                    profile_time = cur_time
                    self.user_name, self.ap_card, self.aka_index = \
                        json_dict['name'], json_dict['appeal'], json_dict['akaname']

            # skill record, maintains highest skill you've achieved
            elif line_type == 'skill':
                if cur_time > skill_time:
                    skill_time = cur_time
                    self.skill = max(json_dict['base'], self.skill)

            # param record, use a uncanny way to store the crew
            elif line_type == 'param':
                if json_dict['type'] == 2 and json_dict['id'] == 1:
                    if cur_time > crew_time:
                        crew_time = cur_time
                        self._crew_index = json_dict['param'][24]

        if not self.last_index:
            timber.error('Music record not found, make sure you have at least played once (and saved successfully).')
            sys.exit(1)

        self.akaname = 'よろしくお願いします'  # Default akaname
        try:
            try:
                self.crew_id = sheet.crew_id[self._crew_index]
            except KeyError:
                self.crew_id = '0014'  # Gen 6 Rasis

            timber.info('Profile data load successfully.\n'
                        'user name   :%s\nappeal card :%d\nakaname     :%s\nskill       :%d\ncrew        :%s' %
                        (self.user_name, self.ap_card, self.akaname, self.skill, self.crew_id))
        except AttributeError:
            timber.error('Profile/Skill/Crew data not found, '
                         'make sure you have at least played once (and saved successfully).')
            sys.exit(1)

        timber.info('Asphyxia database parse complete.')

    def get_akaname(self):
        """Update the akaname through npdb.aka_db, can be removed if necessary"""
        for akaname in aka_db:
            if int(akaname[0]) == self.aka_index:
                self.akaname = akaname[1]
                timber.info('Update akaname data to %s' % self.akaname)
                break

    def get_lv_vf(self, lv_i: int = 8, vf_i: int = 9, wvf_i: int = 10):
        """
        Look up level and calculate vf through npdb.level_table

        :param lv_i: index of level
        :param vf_i: index of volforce
        :param wvf_i: index of weighted volforce, used for B50 sorting
        """
        if self.music_map[self.last_index][lv_i] or self.music_map[self.last_index][vf_i]:
            timber.error('Designed index has been occupied, try another index.')
            sys.exit(1)
        for index in range(len(self.music_map)):
            valid, mid, m_type, score, clear, grade, m_time, exs = self.music_map[index][:8]
            if not valid:
                continue
            try:
                lv = int(level_table[mid][10 + m_type * 3])
            except ValueError:
                lv = 0
            vf = int(lv * 20 * (score / 10000000) * sheet.clear_factor[clear] * sheet.grade_factor[grade]) / 20
            wvf = (vf * 10000 + lv) * 100000000 + score
            self.music_map[index][lv_i], self.music_map[index][vf_i], self.music_map[index][wvf_i] = lv, vf, wvf

    @property
    def profile(self):
        return [self.user_name, self.ap_card, self.akaname, self.skill, self.crew_id]


asp = ASPParser(db_dir=cfg.db_dir, map_size=cfg.map_size, card_num=cfg.card_num)
asp.get_akaname()
asp.get_lv_vf()
