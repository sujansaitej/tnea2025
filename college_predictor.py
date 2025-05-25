
category_list = [
    ['Computer Science and Engineering', 'Computer Science and Engineering (SS)'],
    ['Information Technology', 'Information Technology (SS)'],
    ['Computer Science and Business System', 'Computer Science and Business System (SS)'],
    ['M.Tech. Computer Science and Engineering (Integrated 5 Years)'],
    ['Computer Science and Engineering (Internet of Things and Cyber Security Including Block Chain Technology)',
     'Computer Science and Engineering (Internet of Things)'],
    ['Artificial Intelligence and Data Science',
     'Artificial Intelligence and Data Science (SS)',
     'Computer Science and Engineering (Data Science)'],
    ['Artificial Intelligence and Machine Learning',
     'Computer Science and Engineering (AI and Machine Learning)',
     'Computer Science and Engineering (Artificial Intelligence and Machine Learning) (SS)'],
    ['Computer Science and Engineering (Cyber Security)',
     'Cyber Security',
     'Computer Science and Technology',
     'Computer Science and Design',
     'Computer and Communication Engineering',
     'Computer Science and Engineering (Tamil)'],
    ['Electronics and Communication Engineering',
     'Electronics and Communication Engineering (SS)'],
    ['Electronics Engineering (VLSI Design and Technology)',
     'Electronics Engineering (VLSI Design and Technology) (SS)'],
    ['Electrical and Electronics Engineering',
     'Electrical and Electronics Engineering (SS)',
     'Electrical and Electronics (Sandwich) (SS)'],
    ['Electronics and Instrumentation Engineering',
     'Electronic Instrumentation and Control Engineering'],
    ['Electronics and Communication (Advanced Communication Technology)'],
    ['Electronics and Computer Engineering',
     'Electrical and Computer Engineering'],
    ['Mechanical Engineering',
     'Mechanical Engineering (SS)',
     'Mechanical Engineering (Sandwich) (SS)'],
    ['Mechatronics (SS)', 'Mechatronics Engineering'],
    ['Mechanical and Automation Engineering',
     'Mechanical and Mechatronics Engineering (Additive Manufacturing)'],
    ['Mechanical Engineering (Automobile)',
     'Mechanical Engineering (Tamil Medium)',
     'Mechanical and Smart Manufacturing'],
    ['Automobile Engineering', 'Automobile Engineering (SS)'],
    ['Aeronautical Engineering', 'Aerospace Engineering'],
    ['Production Engineering',
     'Production Engineering (Sandwich) (SS)',
     'Production Engineering (SS)',
     'Robotics and Automation',
     'Robotics and Automation (SS)'],
    ['Metallurgical Engineering', 'Metallurgical Engineering (SS)'],
    ['Material Science and Engineering (SS)'],
    ['Marine Engineering', 'Medical Electronics', 'Mining Engineering', 'Safety and Fire Engineering'],
    ['Manufacturing Engineering', 'Industrial Engineering'],
    ['Civil Engineering',
     'Civil Engineering (SS)',
     'Civil Engineering (Tamil Medium)',
     'Civil Engineering (Environmental Engineering)'],
    ['Geo Informatics'],
    ['Chemical and Electro Chemical Engineering (SS)',
     'Chemical Engineering',
     'Chemical Engineering (SS)'],
    ['Petro Chemical Engineering',
     'Petro Chemical Technology',
     'Petroleum Engineering and Technology (SS)'],
    ['Pharmaceutical Technology',
     'Pharmaceutical Technology (SS)'],
    ['Ceramic Technology (SS)',
     'Leather Technology',
     'Plastic Technology',
     'Rubber and Plastic Technology',
     'Printing & Packing Technology'],
    ['Bio Medical Engineering',
     'Bio Medical Engineering (SS)',
     'Bio Technology',
     'Bio Technology (SS)',
     'Industrial Bio Technology',
     'Industrial Bio Technology (SS)'],
    ['Food Technology',
     'Food Technology (SS)',
     'Agricultural Engineering'],
    ['Interior Design (SS)',
     'Fashion Technology',
     'Fashion Technology (SS)',
     'Apparel Technology (SS)',
     'Handloom and Textile Technology',
     'Textile Technology',
     'Textile Technology (SS)']
]



def category(course):
    # Normalize the input course
    normalized_course = str(course).strip().upper()
    
    for category_items in category_list:
        # Check if any item in category matches (case-insensitive)
        if any(normalized_course == str(item).strip().upper() for item in category_items):
            return category_items
    return [course]

def list_of_colleges(mark, course, community, data):
    course_final = category(course)
    
    # Create a set of normalized course names for comparison
    normalized_course_final = {str(c).strip().upper() for c in course_final}
    
    # Filter using the normalized set
    filtered_data = data[
        data['Branch Name'].str.strip().str.upper().isin(normalized_course_final) & 
        (data[community] <= (mark + 5)) & 
        (data[community] > 0)
    ]
    
    result = filtered_data[['College Code', 'College Name', 'Branch Code', 'Branch Name', community]]
    result = result.sort_values(by=community, ascending=False)
    return result