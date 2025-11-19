-- Function to get franchises available in a specific state
create or replace function get_franchises_by_state (
  filter_state_code text
)
returns table (
  id bigint,
  franchise_name text,
  primary_category text,
  sub_categories jsonb,
  description_text text,
  total_investment_min_usd int,
  image_url text
)
language plpgsql
as $$
begin
  return query (
    select
      f.id,
      f.franchise_name,
      f.primary_category,
      f.sub_categories,
      f.description_text,
      f.total_investment_min_usd,
      -- Use a default placeholder if image_url doesn't exist
      null::text as image_url
    from
      "Franchises" f
    where
      -- 1. Exclude if state is in the static unavailable_states JSON list
      (
         f.unavailable_states is null 
         or not (f.unavailable_states::jsonb ? filter_state_code)
      )
      
      -- 2. Exclude if explicit "Not Available" check exists for this state
      and not exists (
        select 1 from territory_checks tc 
        where tc.franchise_id = f.id 
        and tc.state_code = filter_state_code 
        and tc.availability_status = 'Not Available'
      )
    order by
      f.franchise_name asc
  );
end;
$$;
