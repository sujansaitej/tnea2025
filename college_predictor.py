category_list = [
    ['Computer Science And Engineering', 'Computer Science And Engineering (SS)'],
    ['Information Technology', 'Information Technology (SS)', 'Information Science & Technology'],
    ['Computer Science And Bussiness System', 'Computer Science And Bussiness System (SS)'],
    ['Computer Science And Engineering (Artificial Intelligence And Machine Learning)', 'Computer Science And Engineering (Artificial Intelligence And Machine Learning) (SS)'],
    ['Artificial Intelligence And Data Science', 'Artificial Intelligence And Data Science (SS)'],
    ['Civil Engineering', 'Civil Engineering (SS)'],
    ['Electronics And Communication Engineering', 'Electronics And Communication Engineering (SS)'],
    ['Electrical And Electronics Engineering', 'Electrical And Electronics Engineering (SS)', 'Electrical And Electronics (Sandwich) (SS)'],
    ['Mechanical Engineering (Tamil Medium)'],
    ['Civil Engineering (Tamil Medium)'],
    ['Industrial Engineering'],
    ['Manufacturing Engineering'],
    ['M.Tech. Computer Science And Engineering (Integrated 5 Years)'],
    ['Mechanical Engineering', 'Mechanical Engineering (SS)', 'Mechanical Engineering (Sandwich) (SS)'],
    ['Mechatronics Engineering'],
    ['Robotics And Automation', 'Robotics And Automation (SS)'],
    ['Metallurgical Engineering', 'Metallurgical Engineering (SS)'],
    ['Production Engineering', 'Production Engineering (SS)', 'Production Engineering (Sandwich) (SS)'],
    ['Food Technology', 'Food Technology (SS)'],
    ['Bio Technology', 'Bio Technology (SS)', 'Industrial Bio Technology', 'Industrial Bio Technology (SS)'],
    ['Artificial Intelligence And Machine Learning'],
    ['Automobile Engineering'],
    ['Bio Medical Engineering', 'Bio Medical Engineering (SS)']
    
]
def category(course):
    for category in category_list:
        if course in category:
            return category
    return [course]

def list_of_colleges(mark, course, community, data):
    course_final = category(course)
    filtered_data = data[data['Branch Name'].isin(course_final) & (data[community] <= (mark + 5))]
    result = filtered_data[['College Code', 'College Name','Branch Code', 'Branch Name' , community]]
    result = result.sort_values(by=community, ascending=False)
    return result