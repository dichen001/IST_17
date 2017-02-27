select t_find_closer.*, u.login closer
    from users u
join
    (
    select t_find_submitter.*, u.login submitter
        from users u
    join
        (
        select * from
            (
            select 
                u.login owner,
                repo.owner_id, 
                repo.name repo,
                repo.id repo_id, 
                repo.updated_at,
                pr.id pr_id,
                pr.pullreq_id github_pr_id
                from projects repo,
                pull_requests pr,
                users u
                where pr.id  between 11330000 and 11980000
                and repo.id = pr.base_repo_id
                and repo.forked_from is NULL
                and repo.deleted = 0
                and repo.updated_at > DATE('2016-01-01')
                and u.id = repo.owner_id
            ) t_pr_repo_not_fork_active
        join
            ( 
            select * from (
                select t_pr_created_at_Jan_closed.*, t_pr_has_comment.c_num
                    from
                    (select t_pr_created_in_Jan.pull_request_id, pr_open_date, submitter_id, closer_id
                     from
                        (select id, pull_request_id, created_at pr_open_date, action, actor_id submitter_id from pull_request_history 
                            where pull_request_id  between 11330000 and 11980000
                            and action = 'opened'
                            and created_at between DATE('2016-01-01') and DATE('2016-02-01')
                        )t_pr_created_in_Jan
                     join  
                        (select id, pull_request_id, actor_id closer_id from    
                            (SELECT t_pr_last_action_all.*     
                                FROM pull_request_history t_pr_last_action_all 
                                JOIN
                                    (
                                        SELECT max(id) id, pull_request_id
                                        FROM pull_request_history
                                        where pull_request_id  between 11330000 and 11980000 
                                        GROUP BY pull_request_id
                                    ) t_pr_last_action_part 
                                ON t_pr_last_action_all.id = t_pr_last_action_part.id
                            )t
                          where action = 'closed'  
                        )t_pr_closed  
                     on t_pr_created_in_Jan.pull_request_id = t_pr_closed.pull_request_id
                     ) t_pr_created_at_Jan_closed
                join
                    (select pull_request_id, count(comment_id) c_num   
                        FROM pull_request_comments
                        where pull_request_id  between 11330000 and 11980000 
                        group by pull_request_id
                     ) t_pr_has_comment
                on t_pr_created_at_Jan_closed.pull_request_id = t_pr_has_comment.pull_request_id
            ) t
            where c_num > 9
            ) t_pr_closed_comment_9
        on t_pr_repo_not_fork_active.pr_id = t_pr_closed_comment_9.pull_request_id    
        )t_find_submitter
    on u.id = t_find_submitter.submitter_id    
    )t_find_closer
on u.id = t_find_closer.closer_id
