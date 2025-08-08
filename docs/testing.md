## 测试（Testing）

验收测试（按里程碑）
- M0–M3：`backend-v2/tests/acceptance_m0_m1_m2_m3.py`
- M4：`backend-v2/tests/acceptance_m4.py`
- M5：`backend-v2/tests/acceptance_m5.py`
- M6：`backend-v2/tests/acceptance_m6.py`，`backend-v2/tests/acceptance_m6_universe.py`
- M7：`backend-v2/tests/acceptance_m7.py`

单元测试
- `backend-v2/tests/unit_standardize.py`

如何运行
```bash
cd backend-v2
source .venv/bin/activate
python tests/acceptance_m0_m1_m2_m3.py
python tests/acceptance_m4.py
python tests/acceptance_m5.py
python tests/acceptance_m6.py
python tests/acceptance_m6_universe.py
python tests/acceptance_m7.py
```
