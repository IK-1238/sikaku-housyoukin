// ページ読み込み完了後にイベントを設定
document.addEventListener('DOMContentLoaded', function () {
    const nameInput   = document.getElementById('nameFilter');
    const applyBtn    = document.getElementById('applyFilter');
    const clearBtn    = document.getElementById('clearFilter');
    const table       = document.getElementById('licenseTable');
    const tbody       = table.querySelector('tbody');

    // 絞り込み処理
    function applyFilter() {
        const nameKeyword = nameInput.value.trim().toLowerCase();

        // チェックされているランクを配列で取得
        const checkedRanks = Array.from(
            document.querySelectorAll('input[name="rankFilter"]:checked')
        ).map(cb => cb.value);

        // ★ チェックされている区分を配列で取得
        const checkedKubun = Array.from(
            document.querySelectorAll('input[name="kubunFilter"]:checked')
        ).map(cb => cb.value);

        // 各行を判定
        Array.from(tbody.rows).forEach(row => {
            const nameCell  = row.querySelector('.col-name');
            const rankCell  = row.querySelector('.col-rank');
            const kubunCell = row.querySelector('.col-kubun');  // ★追加

            if (!nameCell || !rankCell || !kubunCell) {
                return;
            }

            const nameText  = nameCell.textContent.toLowerCase();
            const rankText  = rankCell.textContent.trim();
            const kubunText = kubunCell.textContent.trim();

            // 資格名フィルタ（空欄なら常に true）
            const nameMatch  = (nameKeyword === '') || nameText.includes(nameKeyword);

            // ランクフィルタ（チェックなしなら全ランク許可）
            const rankMatch  = (checkedRanks.length === 0) || checkedRanks.includes(rankText);

            // 区分フィルタ（チェックなしなら全区分許可）★追加
            const kubunMatch = (checkedKubun.length === 0) || checkedKubun.includes(kubunText);

            // 3つすべてを満たす行だけ表示
            if (nameMatch && rankMatch && kubunMatch) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    }

    // 絞り込み解除処理
    function clearFilter() {
        nameInput.value = '';

        // ランクのチェックを外す
        document
            .querySelectorAll('input[name="rankFilter"]:checked')
            .forEach(cb => (cb.checked = false));

        // 区分のチェックを外す ★追加
        document
            .querySelectorAll('input[name="kubunFilter"]:checked')
            .forEach(cb => (cb.checked = false));

        // 全行を表示
        Array.from(tbody.rows).forEach(row => {
            row.style.display = '';
        });
    }

    // ボタンにイベントを紐づけ
    if (applyBtn) {
        applyBtn.addEventListener('click', applyFilter);
    }
    if (clearBtn) {
        clearBtn.addEventListener('click', clearFilter);
    }

    // Enterキーで絞り込みたい場合（任意）
    if (nameInput) {
        nameInput.addEventListener('keydown', function (e) {
            if (e.key === 'Enter') {
                applyFilter();
            }
        });
    }
});