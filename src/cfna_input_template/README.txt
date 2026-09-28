CFNA INPUT TEMPLATE
===================

Hand these files to CFNA, either one at a time or together:

  python -m cfna new --title "My case" --file incident_notes.txt --file transactions.csv
  python -m cfna new                      (interactive wizard)
  python -m cfna run <case_dir>           (if you already built the folder yourself)

What matters is the CONTENT, not the file name:

  * narrative .txt/.md/.log  -> free text; identifiers (account, UPI, phone, IMEI,
    ICCID, IFSC, PAN, IP) and role words (kingpin, recruiter, operator, mule,
    victim) are extracted automatically.
  * .csv                     -> kind is sniffed from the header, so
      transactions need amount/txn/debit/credit columns,
      call logs need msisdn/duration/caller/callee,
      SIM registry needs iccid/imei/msisdn,
      device logs need imei/app_version/session/ip_address.
  * .json / .jsonl           -> list of objects, or {"records": [...]}.
  * case.json                -> optional metadata (title, police station, dates).

Every row and every sentence is traceable: the report cites the source file and line.
