import pandas as pd

# --------------------------------------------
# 1.  Master list of programme / branch names
# --------------------------------------------
category_list = [
    ['Computer Science and Engineering', 'Computer Science and Engineering (SS)'],
    ['Information Technology', 'Information Technology (SS)'],
    ['Computer Science and Business System', 'Computer Science and Business System (SS)'],
    ['M.Tech. Computer Science and Engineering (Integrated 5 Years)'],

    ['Artificial Intelligence and Data Science',
     'Artificial Intelligence and Data Science (SS)'],
    ['Computer Science and Engineering (AI and Machine Learning)',
     'Computer Science and Engineering (Artificial Intelligence and Machine Learning) (SS)'],
    ['Computer Science and Engineering (Cyber Security)', 'Cyber Security'],

    ['Electronics and Communication Engineering',
     'Electronics and Communication Engineering (SS)'],
    ['Electronics Engineering (VLSI Design and Technology)',
     'Electronics Engineering (VLSI Design and Technology) (SS)'],
    ['Electrical and Electronics Engineering',
     'Electrical and Electronics Engineering (SS)',
     'Electrical and Electronics (Sandwich) (SS)'],
    ['Electronics and Instrumentation Engineering'],

    ['Mechanical Engineering', 'Mechanical Engineering (SS)', 'Mechanical Engineering (Sandwich) (SS)'],
    ['Mechatronics (SS)', 'Mechatronics Engineering'],
    ['Automobile Engineering', 'Automobile Engineering (SS)'],
    ['Aeronautical Engineering', 'Aerospace Engineering'],
    ['Production Engineering',
     'Production Engineering (Sandwich) (SS)', 'Production Engineering (SS)'],
    ['Robotics and Automation', 'Robotics and Automation (SS)'],
    ['Metallurgical Engineering', 'Metallurgical Engineering (SS)'],
    ['Civil Engineering', 'Civil Engineering (SS)'],

    ['Chemical and Electro Chemical Engineering (SS)'],
    ['Chemical Engineering', 'Chemical Engineering (SS)'],
    ['Pharmaceutical Technology', 'Pharmaceutical Technology (SS)'],

    ['Bio Medical Engineering', 'Bio Medical Engineering (SS)'],
    ['Bio Technology', 'Bio Technology (SS)'],
    ['Industrial Bio Technology', 'Industrial Bio Technology (SS)'],
    ['Food Technology', 'Food Technology (SS)'],

    ['Interior Design (SS)'],
    ['Fashion Technology', 'Fashion Technology (SS)'],
    ['Textile Technology', 'Textile Technology (SS)']
]

# -------------------------------------------------------------
# 2.  Fast lookup table: each variant → the full category list
# -------------------------------------------------------------
_category_lookup = {
    variant.strip().upper(): cat
    for cat in category_list
    for variant in cat
}

# --------------------------------------------------
# 3.  Helper to resolve any course name to its set
# --------------------------------------------------
def category(course):
    """
    Return the full list of course variants that belong to the
    same category as *course*.  If the course isn't recognised,
    return a singleton list containing the original input.
    """
    return _category_lookup.get(str(course).strip().upper(), [course])

# ----------------------------------------------------------------
# 4.  College-filtering helper
# ----------------------------------------------------------------
def list_of_colleges(mark, course, community, data):
    """
    Parameters
    ----------
    mark : int or float
        Candidate’s cut-off / rank / score.
    course : str
        Any variant spelling of the target branch.
    community : str
        Column name in *data* that stores community-wise closing rank.
    data : pandas.DataFrame
        Must contain columns:
        'Branch Name', the *community* column, and for display:
        'College Code', 'College Name', 'Branch Code'.

    Returns
    -------
    pandas.DataFrame
        Filtered and sorted view with columns:
        ['College Code', 'College Name', 'Branch Code', 'Branch Name', community]
    """
    # Resolve every alias that belongs to the requested course
    aliases = {c.strip().upper() for c in category(course)}

    mask = (
        data['Branch Name'].str.strip().str.upper().isin(aliases)
        & (data[community] <= mark + 5)
        & (data[community] > 0)
    )

    cols = ['College Code', 'College Name', 'Branch Code', 'Branch Name', community]
    return (
        data.loc[mask, cols]
            .sort_values(by=community, ascending=False)
            .reset_index(drop=True)
    )
