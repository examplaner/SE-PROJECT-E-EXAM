"""Write prototype3's two input folders, data/tiny and data/main.

    python tools/generate_data.py

Every number comes from docs/data_design_spec.md section 8 and sits in TINY
and MAIN below, so it can be changed and the script run again. The same SEED
always gives the same files.

In order:
  1. sections and students (IDs like BT2CSE0001)
  2. every student gets their cohort's cores, and electives are handed out at
     random so each elective gets exactly the number of students in the spec
  3. every (cohort, subject) gets its own course code; a subject written by
     several cohorts is one paper, so its codes go in constraints.yaml
  4. each paper's sections are split into teaching groups, one teacher each
  5. the files are written, read back and checked with the planner's own
     input checks (validate.py)
"""

import csv
import datetime
import math
import random
import shutil
import sys
from pathlib import Path

import yaml

PROTOTYPE = Path(__file__).resolve().parent.parent
# the planner's modules sit in prototype3/engine/
sys.path.insert(0, str(PROTOTYPE / "engine"))
import loader  # noqa: E402
import validate  # noqa: E402

SEED = 2026

# room type -> (rows, seat columns), model spec section 9
ROOM_SHAPES = {"S": (6, 3), "M": (7, 6)}
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]

# subject key -> (title, department). The department starts the course code.
# The same key in two cohorts is the same question paper; Discrete Maths has
# two keys because BT2 and BT3 write different papers.
SUBJECTS = {
    # BTech 2nd year
    "lade": ("Linear Algebra & Differential Equations", "MTH"),
    "dap": ("Data Analysis using Python", "CSE"),
    "dsa": ("Data Structures & Algorithms", "CSE"),
    "web": ("Web Programming", "CSE"),
    "dld": ("Digital Logic Design", "ECE"),
    "oops": ("OOPS using Java", "CSE"),
    "ie": ("Innovation & Entrepreneurship", "MGT"),
    "sigsys": ("Signals & Systems", "ECE"),
    "sensors_iot": ("Sensors & IoT", "ECE"),
    "robotics_iot": ("Robotics & IoT", "MEC"),
    "thermo": ("Thermodynamics", "MEC"),
    "eng_materials": ("Engineering Materials", "MEC"),
    "dm_bt2": ("Discrete Mathematics", "MTH"),
    "semi_phy": ("Semiconductor Physics", "PHY"),
    "quantum": ("Quantum", "PHY"),
    "modeling_life": ("Modeling Life", "BIO"),
    # BTech 3rd year
    "ml": ("Machine Learning", "CSE"),
    "coa": ("Computer Organization & Architecture", "CSE"),
    "ai": ("Artificial Intelligence", "CSE"),
    "iot": ("IoT", "ECE"),
    "coding_skills": ("Coding Skills", "CSE"),
    "dm_bt3": ("Discrete Mathematics", "MTH"),
    "mpmc": ("Microprocessors & Microcontrollers", "ECE"),
    "vlsi": ("Digital VLSI", "ECE"),
    "ads": ("Advanced Data Science", "CSE"),
    "big_data": ("Big Data", "CSE"),
    "cedha": ("CE&DHA", "CSE"),
    "sad": ("Security Attack & Defence", "CSE"),
    "applied_db": ("Applied Databases", "CSE"),
    # BTech 4th year
    "compiler": ("Compiler Design", "CSE"),
    "plc": ("Automation with PLC", "MEC"),
    "adv_mfg": ("Advanced Manufacturing", "MEC"),
    "agentic_ai": ("Agentic AI", "CSE"),
    "nlp": ("NLP", "CSE"),
    "idt": ("IDT", "CSE"),
    "cyber_forensics": ("Cyber Forensics", "CSE"),
    "sds": ("SDS", "CSE"),
    "cad_vlsi": ("CAD for VLSI", "ECE"),
    "sdm": ("Semiconductor Device Modeling", "ECE"),
    "ev": ("EV Technologies", "MEC"),
    "vehicle_dyn": ("Vehicle Dynamics", "MEC"),
    "cfd": ("CFD", "MEC"),
    "composites": ("Composite Materials", "MEC"),
    # BBA (names from the Phase 0 data)
    "macroecon": ("Macroeconomics", "MGT"),
    "bus_stat": ("Business Statistics", "MGT"),
    "bus_comm": ("Business Communication", "MGT"),
    "finance": ("Finance", "MGT"),
    "marketing": ("Marketing", "MGT"),
    "design_thinking": ("Design Thinking", "HUM"),
    "bus_law": ("Business Law", "LAW"),
    "strat_mgmt": ("Strategic Management", "MGT"),
    "ops_mgmt": ("Operations Management", "MGT"),
    "happiness": ("Happiness", "HUM"),
    "bim": ("Bringing Ideas to Market", "MGT"),
    "ethics": ("Ethics and Integrity in Business", "LAW"),
    "org_beh": ("Organizational Behaviour", "HUM"),
}


def make_cohort(cohort_id, program, year, sections, cores, electives=None, electives_per_student=0):
    """One cohort's design. electives: subject key -> number of students."""
    return {
        "id": cohort_id,
        "program": program,
        "year": year,
        "sections": sections,
        "cores": cores,
        "electives": electives or {},
        "electives_per_student": electives_per_student,
    }


BT2_COMMON = ["lade", "dap", "ie"]

MAIN = {
    "name": "main",
    "section_size": 50,
    "cohorts": [
        make_cohort("BT2CSE", "BTECH", 2, 7, BT2_COMMON + ["dsa", "web", "dld", "oops"],
                    {"dm_bt2": 150, "semi_phy": 90, "quantum": 70, "modeling_life": 40}, 1),
        make_cohort("BT2ECOM", "BTECH", 2, 1,
                    BT2_COMMON + ["dsa", "web", "dld", "sigsys", "sensors_iot"]),
        make_cohort("BT2ME", "BTECH", 2, 1,
                    BT2_COMMON + ["robotics_iot", "thermo", "eng_materials", "sensors_iot"]),
        make_cohort("BT3CSE", "BTECH", 3, 7, ["ml", "coa", "ai", "iot", "coding_skills", "dm_bt3"],
                    {"ads": 160, "big_data": 70, "cedha": 50, "sad": 40, "applied_db": 30}, 1),
        make_cohort("BT3ECOM", "BTECH", 3, 1, ["ml", "coa", "mpmc", "vlsi", "coding_skills"],
                    {"ads": 50}, 1),
        make_cohort("BT4CSE", "BTECH", 4, 7, [],
                    {"agentic_ai": 200, "nlp": 150, "idt": 120, "cyber_forensics": 90,
                     "sad": 80, "sds": 60}, 2),
        make_cohort("BT4ECOM", "BTECH", 4, 1, ["compiler", "big_data"],
                    {"agentic_ai": 30, "nlp": 25, "idt": 20, "cad_vlsi": 15, "sdm": 10}, 2),
        make_cohort("BT4ME", "BTECH", 4, 1, ["plc", "adv_mfg"],
                    {"ev": 35, "vehicle_dyn": 25, "cfd": 25, "composites": 15}, 2),
        make_cohort("BB2", "BBA", 2, 3, ["macroecon", "bus_stat", "bus_comm"],
                    {"finance": 55, "marketing": 55, "design_thinking": 40}, 1),
        make_cohort("BB3", "BBA", 3, 3, ["bus_law", "strat_mgmt", "ops_mgmt", "happiness"],
                    {"bim": 50, "ethics": 50, "org_beh": 50}, 1),
    ],
    "rooms": {"S": 18, "M": 18},
    # 85 teachers: 10 PhD scholars; the other 75 are 20% / 30% / 50%
    "teachers": {"PROF": 15, "ASSOC": 22, "ASST": 38, "PHD": 10},
    # a core paper's sections are split into groups of at most this many
    # sections, and at least 2 groups when it has 2 or more sections
    "max_sections_per_core_group": 3,
    # an elective with this many students or more gets 2 teachers
    "big_elective_size": 150,
    "settings": {
        "start_date": datetime.date(2026, 11, 2),
        "end_date": datetime.date(2026, 11, 20),
        "exam_weekdays": ["Mon", "Tue", "Wed", "Thu", "Fri"],
        "holidays": [datetime.date(2026, 11, 11)],
        "sessions": ["morning", "evening"],
        "min_gap_days": 2,
        "invigilators_per_room": 2,
    },
}

TINY = {
    "name": "tiny",
    "section_size": 8,
    "cohorts": [
        make_cohort("BT2CSE", "BTECH", 2, 1, ["dsa", "oops"], {"dm_bt2": 5, "semi_phy": 3}, 1),
        make_cohort("BT2ECOM", "BTECH", 2, 1, ["dsa", "sigsys"],
                    {"quantum": 5, "modeling_life": 3}, 1),
    ],
    "rooms": {"S": 2, "M": 1},
    "teachers": {"PROF": 2, "ASSOC": 2, "ASST": 4, "PHD": 1},
    "max_sections_per_core_group": 3,
    "big_elective_size": 150,
    "settings": {
        "start_date": datetime.date(2026, 11, 2),
        "end_date": datetime.date(2026, 11, 6),
        "exam_weekdays": ["Mon", "Tue", "Wed", "Thu", "Fri"],
        "holidays": [],
        "sessions": ["morning", "evening"],
        "min_gap_days": 2,
        "invigilators_per_room": 2,
    },
}

DATASETS = [TINY, MAIN]


class DesignError(Exception):
    """The numbers of a dataset design don't add up."""


def main():
    failed = False
    for design in DATASETS:
        out_dir = PROTOTYPE / "data" / design["name"]
        print(f"{design['name']}: writing {out_dir}")
        try:
            codes, registrations, assigned, teachers = build_dataset(design, out_dir)
        except DesignError as error:
            print(f"  design error: {error}")
            failed = True
            continue
        print_summary(design, codes, registrations, assigned, teachers)
        problems = check_folder(out_dir)
        if problems:
            failed = True
            # indent every line of the report under the dataset's name
            print("  " + validate.format_report(problems).replace("\n", "\n  "))
        else:
            print("  checks passed")
    if failed:
        return 1
    return 0


def build_dataset(design, out_dir):
    """Write one input folder. Returns what print_summary() needs."""
    rng = random.Random(SEED)
    section_rows, students_by_section, students_by_cohort = make_sections_and_students(design)
    codes = make_course_codes(design)

    # every core, plus the electives handed out
    registrations = []
    for cohort in design["cohorts"]:
        chosen = allocate_electives(cohort["id"], students_by_cohort[cohort["id"]],
                                    cohort["electives"], cohort["electives_per_student"], rng)
        for student in students_by_cohort[cohort["id"]]:
            for subject in cohort["cores"] + chosen[student]:
                registrations.append((student, codes[(cohort["id"], subject)]))

    groups = make_teaching_groups(design, codes, registrations, students_by_section)
    teachers = make_teachers(design)
    assigned = assign_teachers(groups, teachers, rng)
    teaching_rows = make_teaching_rows(assigned, codes, registrations, students_by_section)

    # write everything fresh
    if out_dir.exists():
        shutil.rmtree(out_dir)
    (out_dir / "sections").mkdir(parents=True)

    write_csv(out_dir / "sections.csv", loader.CSV_COLUMNS["sections"], section_rows)
    for section_id, members in students_by_section.items():
        write_csv(out_dir / "sections" / f"{section_id}.csv", loader.ROSTER_COLUMNS,
                  [[student] for student in members])
    write_csv(out_dir / "courses.csv", loader.CSV_COLUMNS["courses"],
              make_course_rows(design, codes))
    write_csv(out_dir / "registrations.csv", loader.CSV_COLUMNS["registrations"], registrations)
    write_csv(out_dir / "rooms.csv", loader.CSV_COLUMNS["rooms"], make_room_rows(design))
    write_csv(out_dir / "teachers.csv", loader.CSV_COLUMNS["teachers"], teachers)
    write_csv(out_dir / "teaching.csv", loader.CSV_COLUMNS["teaching"], teaching_rows)
    write_yaml(out_dir / "settings.yaml", design["settings"])
    write_yaml(out_dir / "constraints.yaml", {"same_paper": same_paper_groups(design, codes)})
    return codes, registrations, assigned, teachers


def make_sections_and_students(design):
    """Returns (rows of sections.csv, {section_id: students},
    {cohort_id: students}). Roll numbers run on across a cohort's sections."""
    section_rows = []
    students_by_section = {}
    students_by_cohort = {}
    for cohort in design["cohorts"]:
        if cohort["sections"] > len(ROMAN):
            raise DesignError(f"{cohort['id']}: more than {len(ROMAN)} sections")
        number = 1
        students_by_cohort[cohort["id"]] = []
        for index in range(cohort["sections"]):
            section_id = f"{cohort['id']}_{ROMAN[index]}"
            section_rows.append([section_id, cohort["id"], cohort["program"], cohort["year"]])
            members = []
            for _ in range(design["section_size"]):
                members.append(f"{cohort['id']}{number:04d}")
                number += 1
            students_by_section[section_id] = members
            students_by_cohort[cohort["id"]].extend(members)
    return section_rows, students_by_section, students_by_cohort


def allocate_electives(cohort_id, students, electives, per_student, rng):
    """Give each student `per_student` different electives, with the exact
    number of students per elective.

    The elective names are laid out in one long list, one block per elective
    (150 x dm_bt2, then 90 x semi_phy, ...). The students are shuffled, and
    list position i goes to student number i mod n. With 2 electives each, a
    student gets positions i and i + n, which are always different electives,
    because no elective has more than n students."""
    result = {student: [] for student in students}
    if per_student == 0:
        if electives:
            raise DesignError(f"{cohort_id}: has electives but 0 electives per student")
        return result

    n = len(students)
    total = sum(electives.values())
    if total != n * per_student:
        raise DesignError(f"{cohort_id}: elective sizes add up to {total}, "
                          f"but {n} students x {per_student} = {n * per_student}")
    for name, count in electives.items():
        if count < 1 or count > n:
            raise DesignError(f"{cohort_id}: elective {name} has {count} students, "
                              f"must be between 1 and {n}")

    labels = []
    for name, count in electives.items():
        labels.extend([name] * count)
    order = list(students)
    rng.shuffle(order)
    for i, label in enumerate(labels):
        result[order[i % n]].append(label)
    return result


def make_course_codes(design):
    """{(cohort_id, subject): course_code}. A code is the department, the
    year digit and a counter per department and year, like CSE2003, so a
    subject in two cohorts gets two codes."""
    counters = {}
    codes = {}
    for cohort in design["cohorts"]:
        for subject in cohort["cores"] + list(cohort["electives"]):
            if subject not in SUBJECTS:
                raise DesignError(f"{cohort['id']}: unknown subject {subject}")
            if (cohort["id"], subject) in codes:
                raise DesignError(f"{cohort['id']}: subject {subject} listed twice")
            _, department = SUBJECTS[subject]
            key = (department, cohort["year"])
            counters[key] = counters.get(key, 0) + 1
            codes[(cohort["id"], subject)] = f"{department}{cohort['year']}{counters[key]:03d}"
    return codes


def subjects_in_order(design):
    """Every subject used, in the order it first appears in the design."""
    seen = []
    for cohort in design["cohorts"]:
        for subject in cohort["cores"] + list(cohort["electives"]):
            if subject not in seen:
                seen.append(subject)
    return seen


def codes_of_subject(codes, subject):
    """[(cohort_id, code), ...] of one subject, in cohort order."""
    found = []
    for (cohort_id, other), code in codes.items():
        if other == subject:
            found.append((cohort_id, code))
    return found


def split_evenly(items, parts):
    """Split a list into `parts` chunks in order, bigger chunks first:
    7 items into 3 parts gives sizes 3, 2, 2."""
    chunks = []
    start = 0
    for part in range(parts):
        size = len(items) // parts
        if part < len(items) % parts:
            size += 1
        chunks.append(items[start:start + size])
        start += size
    return chunks


def make_teaching_groups(design, codes, registrations, students_by_section):
    """Split each paper's sections into groups, one teacher per group.
    Returns [(subject, [section_id, ...]), ...].

    A core paper with one section is one group; with more, groups of at most
    max_sections_per_core_group sections and at least 2 groups. An elective
    paper (any of its codes is an elective) gets 2 groups if it has
    big_elective_size students or more in total, otherwise 1."""
    kind_of = {}
    for cohort in design["cohorts"]:
        for subject in cohort["cores"]:
            kind_of[(cohort["id"], subject)] = "CORE"
        for subject in cohort["electives"]:
            kind_of[(cohort["id"], subject)] = "ELECTIVE"

    registered = set(registrations)
    groups = []
    for subject in subjects_in_order(design):
        paper_codes = codes_of_subject(codes, subject)
        is_core = all(kind_of[(cohort_id, subject)] == "CORE" for cohort_id, _ in paper_codes)

        sections = []
        students = 0
        for cohort_id, code in paper_codes:
            for section_id, members in students_by_section.items():
                if not section_id.startswith(cohort_id + "_"):
                    continue
                writers = 0
                for student in members:
                    if (student, code) in registered:
                        writers += 1
                if writers:
                    sections.append(section_id)
                    students += writers

        if not is_core:
            parts = 2 if students >= design["big_elective_size"] else 1
        elif len(sections) == 1:
            parts = 1
        else:
            parts = max(2, math.ceil(len(sections) / design["max_sections_per_core_group"]))
        parts = min(parts, len(sections))

        for chunk in split_evenly(sections, parts):
            groups.append((subject, chunk))
    return groups


def make_teachers(design):
    """[(teacher_id, rank), ...]: PROF first, then ASSOC, ASST, PHD."""
    teachers = []
    number = 1
    for rank in validate.TEACHER_RANKS:
        for _ in range(design["teachers"].get(rank, 0)):
            teachers.append((f"T{number:03d}", rank))
            number += 1
    return teachers


def assign_teachers(groups, teachers, rng):
    """Give each teaching group one teacher who is not a PhD scholar.
    Returns [(teacher_id, subject, [section_id, ...]), ...].

    Groups are taken in a shuffled order. Each goes to the teacher with the
    fewest groups so far who doesn't already teach that paper, so a split
    paper really has different teachers. Ties go to the earlier teacher in a
    shuffled list, which mixes the ranks."""
    faculty = [teacher_id for teacher_id, rank in teachers if rank != "PHD"]
    if not faculty:
        raise DesignError("no non-PhD teachers to teach")
    rng.shuffle(faculty)
    load = {teacher_id: 0 for teacher_id in faculty}
    papers_of = {teacher_id: set() for teacher_id in faculty}

    order = list(groups)
    rng.shuffle(order)
    assigned = []
    for subject, sections in order:
        candidates = [teacher_id for teacher_id in faculty if subject not in papers_of[teacher_id]]
        if not candidates:
            raise DesignError(f"not enough teachers for paper {subject}")
        # the teacher with the fewest papers so far; on a tie the first one
        teacher = candidates[0]
        for teacher_id in candidates[1:]:
            if load[teacher_id] < load[teacher]:
                teacher = teacher_id
        load[teacher] += 1
        papers_of[teacher].add(subject)
        assigned.append((teacher, subject, sections))
    return assigned


def make_teaching_rows(assigned, codes, registrations, students_by_section):
    """Rows of teaching.csv, sorted: only where the section really has
    students writing the code."""
    registered = set(registrations)
    rows = []
    for teacher, subject, sections in assigned:
        for section_id in sections:
            # BT2CSE_I -> BT2CSE
            cohort_id = section_id.rsplit("_", 1)[0]
            code = codes[(cohort_id, subject)]
            for student in students_by_section[section_id]:
                if (student, code) in registered:
                    rows.append([teacher, code, section_id])
                    break
    rows.sort()
    return rows


def make_course_rows(design, codes):
    rows = []
    for cohort in design["cohorts"]:
        for subject in cohort["cores"]:
            title, _ = SUBJECTS[subject]
            rows.append([codes[(cohort["id"], subject)], title, cohort["id"], "CORE"])
        for subject in cohort["electives"]:
            title, _ = SUBJECTS[subject]
            rows.append([codes[(cohort["id"], subject)], title, cohort["id"], "ELECTIVE"])
    return rows


def make_room_rows(design):
    """S01, S02, ..., then M01, M02, ..."""
    rows = []
    for room_type in ["S", "M"]:
        seat_rows, seat_columns = ROOM_SHAPES[room_type]
        for number in range(1, design["rooms"].get(room_type, 0) + 1):
            rows.append([f"{room_type}{number:02d}", room_type, seat_rows, seat_columns])
    return rows


def same_paper_groups(design, codes):
    """The codes of each subject written by more than one cohort."""
    groups = []
    for subject in subjects_in_order(design):
        group = [code for _, code in codes_of_subject(codes, subject)]
        if len(group) >= 2:
            groups.append(group)
    return groups


# every file ends its lines with \n on every system, as git stores them, so
# running the generator again leaves git with nothing to show
def write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def write_yaml(path, content):
    with open(path, "w", newline="\n", encoding="utf-8") as file:
        yaml.safe_dump(content, file, sort_keys=False, default_flow_style=None)


def check_folder(folder):
    """The planner's input checks on a written folder; empty means fine."""
    paths = loader.input_paths(folder)
    problems = validate.check_files(paths)
    if problems:
        return problems
    return validate.check_data(loader.load(paths))


def print_summary(design, codes, registrations, assigned, teachers):
    students_per_code = {}
    for _, code in registrations:
        students_per_code[code] = students_per_code.get(code, 0) + 1
    teachers_per_subject = {}
    for teacher, subject, _ in assigned:
        teachers_per_subject.setdefault(subject, []).append(teacher)

    sections = sum(cohort["sections"] for cohort in design["cohorts"])
    total_students = sections * design["section_size"]
    print(f"  {total_students} students, {len(codes)} course codes, "
          f"{len(subjects_in_order(design))} papers, {len(teachers)} teachers")
    print(f"  {'paper':<40} {'students':>8}  teachers  codes")
    for subject in subjects_in_order(design):
        paper_codes = [code for _, code in codes_of_subject(codes, subject)]
        students = sum(students_per_code.get(code, 0) for code in paper_codes)
        title, _ = SUBJECTS[subject]
        print(f"  {title:<40} {students:>8}  "
              f"{len(teachers_per_subject.get(subject, [])):>8}  {', '.join(paper_codes)}")

    load = {}
    for teacher, _, _ in assigned:
        load[teacher] = load.get(teacher, 0) + 1
    # number of paper groups -> number of teachers (not PhD) teaching that many
    counts = {}
    for teacher_id, rank in teachers:
        if rank != "PHD":
            groups = load.get(teacher_id, 0)
            counts[groups] = counts.get(groups, 0) + 1
    parts = []
    for groups, teachers_with_that_many in sorted(counts.items()):
        parts.append(f"{teachers_with_that_many} teach {groups} paper group(s)")
    spread = ", ".join(parts)
    print(f"  teaching load (non-PhD): {spread}")


if __name__ == "__main__":
    sys.exit(main())
