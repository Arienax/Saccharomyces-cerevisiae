# non-local packages
import os
import re
import sys
import time
from traceback import format_exc

# interior packages
from utli.logger import timber
from utli import draft, sheet
from genre import packet

VERSION = [1, 2, 2]

class SDVX:
    def __init__(self):
        try:
            self.plot_skin = packet['gen6'].main
            # 直接从出图模块获取实例，彻底脱离旧 parse 模块
            self.asp = self.plot_skin.current_asp
            self.db_reader = self.plot_skin.db_reader
            self.fake_table = self.plot_skin.fake_table
        except KeyError:
            timber.error('Invalid skin name, please check your configurations.')
            sys.exit(1)

    def _get_b50(self):
        print(self.plot_skin.plot_b50())
        input(draft.CommonMsg.enter())

    def _get_summary(self, base_lv: int):
        print(self.plot_skin.plot_summary(base_lv=base_lv))
        input(draft.CommonMsg.enter())

    def _get_single(self, sg_index: int):
        print(self.plot_skin.plot_single(sg_index=sg_index))
        input(draft.CommonMsg.enter())

    def _get_level(self, level: int, limits: tuple, grade_flag: str):
        print(self.plot_skin.plot_level(level=level, limits=limits, grade_flag=grade_flag))
        input(draft.CommonMsg.enter())

    def _1_get_b50(self):
        os.system('cls')
        self._get_b50()

    def _2_get_summary(self):
        os.system('cls')
        base_lv = input(draft.TwoGetSummary.init_hint())
        timber.debug('Get summary from level "%s"' % base_lv)

        if not base_lv:
            self._get_summary(17)
            return

        try:
            base_lv = int(base_lv)
            if base_lv > 20 or base_lv < 1:
                raise ValueError
        except ValueError:
            timber.warning('Invalid level number')
            print(draft.CommonMsg.invalid_lv_num())
            input(draft.CommonMsg.enter())
            return
        self._get_summary(base_lv)

    def _3_get_recent(self):
        # API 暂时无法获取精确的时间戳，屏蔽该功能
        print("当前 API 模式暂不支持获取最近一次游玩记录。")
        input(draft.CommonMsg.enter())

    def _4_get_specific(self):
        def not_found_handler():
            timber.debug('Record not found.')
            input(draft.FourGetSpecific.not_found())

        sg_index = 0
        sep_arg = input(draft.FourGetSpecific.init_hint()).split()
        timber.debug('Get specific "%s"' % ' '.join(sep_arg))

        if len(sep_arg) == 1:
            try:
                mid = int(sep_arg[0])
            except ValueError:
                timber.warning('Invalid character')
                print(draft.FourGetSpecific.invalid_char())
                input(draft.CommonMsg.enter())
                return
            for lv_index in range(4, -1, -1):
                index = mid * 5 + lv_index
                if len(self.asp.music_map) > index and self.asp.music_map[index][0]:
                    sg_index = index
                    break

        elif len(sep_arg) == 2:
            try:
                mid, m_type = int(sep_arg[0]), int(sep_arg[1])
            except ValueError:
                timber.warning('Invalid character')
                print(draft.FourGetSpecific.invalid_char())
                input(draft.CommonMsg.enter())
                return

            if m_type >= 4:
                mxm_index = mid * 5 + m_type
                inf_index = mid * 5 + m_type - 1
                if len(self.asp.music_map) > mxm_index and self.asp.music_map[mxm_index][0]:
                    sg_index = mxm_index
                elif len(self.asp.music_map) > inf_index and self.asp.music_map[inf_index][0]:
                    sg_index = inf_index
            elif m_type > 0:
                index = mid * 5 + m_type - 1
                if len(self.asp.music_map) > index and self.asp.music_map[index][0]:
                    sg_index = index
        else:
            timber.warning('Excessive operator')
            print(draft.FourGetSpecific.invalid_arg_num())
            input(draft.CommonMsg.enter())
            return

        if not sg_index:
            not_found_handler()
            return

        print(draft.FourGetSpecific.search_res(sep_arg))
        self._get_single(sg_index)

    def _5_get_level(self):
        os.system('cls')
        level = input(draft.FiveGetLevel.init_hint())
        try:
            level = int(level)
            if level > 20 or level < 1:
                raise ValueError
        except ValueError:
            timber.warning('Invalid input')
            print(draft.CommonMsg.invalid_lv_num())
            input(draft.CommonMsg.enter())
            return

        threshold = input(draft.FiveGetLevel.threshold()).upper().replace('P', '+')

        if not threshold:
            limits, grade_flag = (0, 10000000), 'ALL'
            print(draft.FiveGetLevel.all_songs(level))
        else:
            try:
                limits = sheet.score_table[threshold]
                grade_flag = threshold
            except KeyError:
                limits = threshold.split('-')
                if len(limits) != 2:
                    print(draft.FiveGetLevel.invalid_sep())
                    input(draft.CommonMsg.enter())
                    return
                try:
                    lim_1, lim_2 = int(limits[0]), int(limits[1])
                    if lim_1 > 10000000 or lim_1 < 0 or lim_2 > 10000000 or lim_2 < 0:
                        raise ValueError('')
                except ValueError:
                    print(draft.FiveGetLevel.invalid_score())
                    input(draft.CommonMsg.enter())
                    return
                limits, grade_flag = (min(lim_1, lim_2), max(lim_1, lim_2)), None

            if grade_flag:
                print(draft.FiveGetLevel.grade_songs(level, grade_flag))
            else:
                print(draft.FiveGetLevel.limit_songs(level, limits[0], limits[1]))
        self._get_level(level, limits, grade_flag)

    def _8_search(self):
        os.system('cls')
        search_str = input(draft.EightSearch.init_hint())

        if search_str:
            result_list = []
            # 改为直接使用 db_reader 搜索
            for mid, song in self.db_reader.music_db.items():
                title = song.get('info', {}).get('title_name', '')
                artist = song.get('info', {}).get('artist_name', '')
                search_target = f"{title} {artist}"
                
                try:
                    if re.search(search_str, search_target, re.I):
                        result_list.append(mid)
                except re.error:
                    print(draft.EightSearch.re_crash())
                    input(draft.CommonMsg.enter())
                    return

            search_res = ['%d result(s) found:\n'
                          '|No  |MID   |Level        |Name  -  Artist' % len(result_list)]
            for index, _mid in enumerate(result_list):
                _data = self.fake_table[_mid]
                search_res.append('\n|%-4d|%-4d  |%s/%s/%s/%s  |%s  -  %s' %
                                  (index + 1, _mid, _data[10].zfill(2), _data[13].zfill(2), _data[16].zfill(2),
                                   str(int(_data[19]) + int(_data[22])).zfill(2), _data[1], _data[3]))

            res_num = len(result_list)
            search_res = ''.join(search_res)

            if res_num:
                print(draft.EightSearch.success(res_num, search_res))
            else:
                print(draft.EightSearch.failed())
        else:
            print(draft.EightSearch.empty())
        input(draft.CommonMsg.enter())

    @staticmethod
    def _9_faq():
        os.system('cls')
        print("本查分器已修改为 API 模式。")
        input(draft.CommonMsg.enter())

    def _0_see_you_next_time(self):
        print(draft.ZeroExit.farewell(self.asp.user_name))
        time.sleep(1.5)
        sys.exit(0)

    @staticmethod
    def _10_donate():
        os.system('cls')
        print(draft.TenDonate.init_hint())
        input(draft.TenDonate.back_to_light())

    def input_handler(self):
        key_dict = {
            '1': self._1_get_b50,
            '2': self._2_get_summary,
            '3': self._3_get_recent,
            '4': self._4_get_specific,
            '5': self._5_get_level,
            '8': self._8_search,
            '9': self._9_faq,
            '0': self._0_see_you_next_time,
            '10': self._10_donate
        }
        os.system('cls')
        time.sleep(0.05)
        print(draft.TitleMsg.title(VERSION), end='')
        while True:
            base_arg = input()
            try:
                key_dict[base_arg]()
                break
            except KeyError:
                pass

if __name__ == '__main__':
    try:
        sdvx = SDVX()
        while True:
            sdvx.input_handler()
    except Exception:
        timber.error('Fatal error occurs.\n%s' % format_exc())
        sys.exit(1)